"""Desktop GUI for the 8-bit floating-point converter (CustomTkinter)."""

import customtkinter as ctk

from converter import ConversionError, decode, describe, encode, format_value

ACCENT = "#eb05ae"
ACCENT_HOVER = "#a8057d"
ERROR = "#ff6b6b"
MUTED = "#a0a0a0"

MODE_TO_DECIMAL = "Binary → Decimal"
MODE_TO_BINARY = "Decimal → Binary"

TITLE_FONT = ("Arial", 26, "bold")
LABEL_FONT = ("Arial", 18)
ENTRY_FONT = ("Consolas", 30, "bold")
RESULT_FONT = ("Arial", 28, "bold")
DETAIL_FONT = ("Arial", 16)


class ConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("8-bit Floating-Point Converter")
        self.geometry("760x520")
        self.resizable(False, False)

        ctk.CTkLabel(self, text="8-bit Floating-Point Converter", font=TITLE_FONT).pack(pady=(24, 4))
        ctk.CTkLabel(
            self, text="sign (1 bit) | exponent (3 bits, excess-4) | mantissa (4 bits)",
            font=DETAIL_FONT, text_color=MUTED,
        ).pack()

        self.mode = ctk.CTkSegmentedButton(
            self, values=[MODE_TO_DECIMAL, MODE_TO_BINARY], font=LABEL_FONT,
            selected_color=ACCENT, selected_hover_color=ACCENT_HOVER, command=self._on_mode_change,
        )
        self.mode.set(MODE_TO_DECIMAL)
        self.mode.pack(pady=20)

        self.prompt = ctk.CTkLabel(self, font=LABEL_FONT)
        self.prompt.pack()

        self.entry = ctk.CTkEntry(
            self, font=ENTRY_FONT, width=260, height=60, justify="center",
            validate="key", validatecommand=(self.register(self._validate), "%P"),
        )
        self.entry.pack(pady=12)

        ctk.CTkButton(
            self, text="Convert", font=LABEL_FONT, width=200, height=44, corner_radius=10,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self.convert,
        ).pack(pady=8)

        self.result = ctk.CTkLabel(self, text="", font=RESULT_FONT)
        self.result.pack(pady=(18, 4))
        self.detail = ctk.CTkLabel(self, text="", font=DETAIL_FONT, text_color=MUTED)
        self.detail.pack()

        self.bind("<Return>", lambda _event: self.convert())
        self._on_mode_change(MODE_TO_DECIMAL)

    # --- input handling -------------------------------------------------
    def _validate(self, proposed: str) -> bool:
        """Block invalid keystrokes: only 0/1 (max 8) in binary mode."""
        if self.mode.get() == MODE_TO_DECIMAL:
            return len(proposed) <= 8 and set(proposed) <= {"0", "1"}
        return len(proposed) <= 16

    def _on_mode_change(self, mode: str):
        self.entry.delete(0, "end")
        self._show("", "")
        if mode == MODE_TO_DECIMAL:
            self.prompt.configure(text="Enter 8 bits, e.g. 01101011")
        else:
            self.prompt.configure(text="Enter a number, e.g. 2.75, -0.375 or 3/8")
        self.entry.focus_set()

    def _show(self, result: str, detail: str, error: bool = False):
        self.result.configure(text=result, text_color=ERROR if error else ("black", "white"))
        self.detail.configure(text=detail)

    # --- conversion -----------------------------------------------------
    def convert(self):
        text = self.entry.get()
        try:
            if self.mode.get() == MODE_TO_DECIMAL:
                self._show(format_value(decode(text)), describe(text))
            else:
                encoding = encode(text)
                detail = describe(encoding.bits)
                if not encoding.exact:
                    detail += (
                        f"\nTruncation error: stored value is {format_value(encoding.stored)}"
                        f" (lost {format_value(encoding.truncation_error)})"
                    )
                self._show(f"{encoding.bits[0]} {encoding.bits[1:4]} {encoding.bits[4:]}", detail)
        except ConversionError as exc:
            self._show("Invalid input", str(exc), error=True)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ConverterApp().mainloop()
