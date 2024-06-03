from PySide6.QtGui import QValidator


class NotEmptyValidator(QValidator):
    def validate(self, input, pos):
        if len(input) > 0:
            return (QValidator.Acceptable, input, pos)
        else:
            return (QValidator.Intermediate, input, pos)


class NameValidator(NotEmptyValidator):
    pass

class AbenteuerValidator(QValidator):
    def validate(self, input, pos):
        abks = input.split(",")
        for abk in abks:
            if len(abk.strip()) > 5:
                return (QValidator.Intermediate, input, pos)
        return (QValidator.Acceptable, input, pos)