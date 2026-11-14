import ast
import operator

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def ev(node):
    if isinstance(node, ast.Expression):
        return ev(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        return OPS[type(node.op)](ev(node.left), ev(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](ev(node.operand))
    raise ValueError("bad expression")


def calculate(text):
    text = text.replace("×", "*").replace("÷", "/")
    result = ev(ast.parse(text, mode="eval"))
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    elif isinstance(result, float):
        result = round(result, 10)
    return str(result)


class CalculatorApp(App):
    def build(self):
        self.title = "Calculator"
        root = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.display = Label(text="0", font_size="48sp", halign="right",
                             valign="middle", size_hint=(1, 0.25))
        self.display.bind(size=lambda w, s: setattr(w, "text_size", s))
        root.add_widget(self.display)

        grid = GridLayout(cols=4, spacing=8, size_hint=(1, 0.75))
        keys = ["C", "⌫", "%", "÷",
                "7", "8", "9", "×",
                "4", "5", "6", "-",
                "1", "2", "3", "+",
                "0", ".", "=", ""]
        for k in keys:
            if k == "":
                grid.add_widget(Label())
                continue
            grid.add_widget(Button(text=k, font_size="28sp",
                                   on_press=self.on_key))
        root.add_widget(grid)
        return root

    def on_key(self, btn):
        key = btn.text
        cur = self.display.text
        if key == "C":
            self.display.text = "0"
        elif key == "⌫":
            self.display.text = cur[:-1] or "0"
        elif key == "=":
            try:
                self.display.text = calculate(cur)
            except Exception:
                self.display.text = "Error"
        elif key == "%":
            try:
                self.display.text = calculate(f"({cur})/100")
            except Exception:
                self.display.text = "Error"
        else:
            if cur in ("0", "Error") and key not in ("÷", "×", "-", "+", "."):
                self.display.text = key
            else:
                self.display.text = cur + key


if __name__ == "__main__":
    CalculatorApp().run()
