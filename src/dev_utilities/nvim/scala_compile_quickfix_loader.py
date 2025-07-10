# this requires:
# .jvmopts
# -Dsbt.log.noformat=true

import os
import re
from dataclasses import dataclass, replace

from pynvim import attach
from slugify import slugify


@dataclass
class ErrorItem:
    path: str
    row: int
    column: int
    message: str = ""

    def to_string(self):
        return f"{self.path}:{self.row}:{self.column}\n\n{self.message}"


def run():
    output_file = f"{os.environ.get('PROJECT_PATH')}/{os.environ.get('COMPILATION_FILE_RESULT', 'errors-l')}.txt"
    if os.path.exists(output_file):
        os.remove(output_file)

    nvim_socket = f"/tmp/{slugify(os.getcwd())}"

    input_file = (
        f"{os.environ.get('PROJECT_PATH')}/{os.environ.get('PROJECT_FILE_TO_READ')}"
    )
    if os.path.exists(input_file):
        log = open(input_file).readlines()
        error_prefix = "[error] "
        errorLineA = re.compile(
            r"-- Error: (?P<filePath>.+):(?P<line>\d+):(?P<column>\d+)"
        )
        errorLineB = re.compile(
            r"-- \[(?P<errorCode>E\d+)\] (.+): (?P<filePath>.+):(?P<line>\d+):(?P<column>\d+)"
        )

        def is_A_or_B(line):
            return errorLineA.search(line) or errorLineB.search(line)

        result = []
        for l in log:
            if l.startswith(error_prefix):
                result.append(l[len(error_prefix) :])

        out_puts = []
        current_entry = None
        creatingEntry = False
        for l in result:
            m = is_A_or_B(l)
            if m:
                if creatingEntry:
                    out_puts.append(current_entry)
                    current_entry = ErrorItem(
                        m.group("filePath"), m.group("line"), m.group("column")
                    )
                else:
                    creatingEntry = True
                    current_entry = ErrorItem(
                        m.group("filePath"), m.group("line"), m.group("column")
                    )
            else:
                if creatingEntry:
                    current_entry = replace(
                        current_entry, **{"message": f"{current_entry.message}{l}"}
                    )

        if current_entry:
            out_puts.append(current_entry)

        if len(out_puts) > 0:
            out_puts.append(out_puts[-1])

        out = "".join(map(lambda x: x.to_string(), out_puts))

        open(output_file, "w").write(out)
        nvim = attach("socket", path=nvim_socket)
        nvim.command(":lua require('run-cmd').loadQuickFix()")
    else:
        open(output_file, "w").write("")
