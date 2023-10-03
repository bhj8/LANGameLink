import tkinter as tk

class LabeledInput(tk.Frame):
    def __init__(self, parent, label_text, value, validator=None, readonly=False, **kwargs):
        super().__init__(parent, **kwargs)
        self.var = tk.StringVar(value=value)
        self.validator = validator

        tk.Label(self, text=label_text).grid(row=0, column=0, pady=5)
        self.entry = tk.Entry(self, textvariable=self.var)
        if readonly:  # 如果只读模式为真，则设置输入框状态为只读
            self.entry.config(state='readonly')
        self.entry.grid(row=0, column=1, pady=5)

        self.warning_label = tk.Label(self, text="格式错误❗", fg="red")
        if validator:
            self.var.trace("w", self.validate)
            self.validate()

    def validate(self, *args):
        if self.validator and not self.validator(self.var.get()):
            self.warning_label.grid(row=0, column=2, pady=5)
        else:
            self.warning_label.grid_remove()
