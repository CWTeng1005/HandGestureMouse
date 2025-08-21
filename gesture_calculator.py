import tkinter as tk, ast

_BIN = {
    ast.Add: lambda a,b:a+b, ast.Sub: lambda a,b:a-b,
    ast.Mult:lambda a,b:a*b, ast.Div: lambda a,b:a/b,
    ast.FloorDiv:lambda a,b:a//b, ast.Mod:lambda a,b:a%b,
    ast.Pow: lambda a,b:a**b,
}
_UN = {ast.UAdd:lambda a:+a, ast.USub:lambda a:-a}

def _ev(n):
    if isinstance(n, ast.Expression):
        return _ev(n.body)
    if isinstance(n, ast.BinOp) and type(n.op) in _BIN:
        return _BIN[type(n.op)](_ev(n.left), _ev(n.right))
    if isinstance(n, ast.UnaryOp) and type(n.op) in _UN:
        return _UN[type(n.op)](_ev(n.operand))
    if isinstance(n, (ast.Num, ast.Constant)) and isinstance(getattr(n,'n',getattr(n,'value',None)), (int,float)):
        return n.n if hasattr(n,'n') else n.value
    raise ValueError("unsupported")
def safe_eval(s:str)->float:
    s=s.strip()
    if not s:
        return 0.0
    return float(_ev(ast.parse(s, mode="eval")))

class GestureCalculator:
    def __init__(self, master=None, topmost=True):
        self._owns = master is None
        self.root = tk.Tk() if self._owns else tk.Toplevel(master)
        self.root.title("Simple Calculator")
        try:
            self.root.attributes("-topmost", bool(topmost))
        except:
            pass
        self.var = tk.StringVar(value="")
        self._build()

    def _build(self):
        f = tk.Frame(self.root, padx=8, pady=8); f.pack(fill="both", expand=True)
        e = tk.Entry(f, textvariable=self.var, font=("Segoe UI",18), justify="right", bd=4, relief="groove")
        e.grid(row=0, column=0, columnspan=4, sticky="nsew", pady=(0,8))
        for i in range(1,6):
            f.rowconfigure(i, weight=1)
        for j in range(4):
            f.columnconfigure(j, weight=1)
        mk=lambda t,c,r,col: tk.Button(f,text=t,command=c,font=("Segoe UI",16)).grid(row=r,column=col,sticky="nsew",padx=4,pady=4)
        mk("7", lambda:self._a("7"),1,0); mk("8", lambda:self._a("8"),1,1); mk("9", lambda:self._a("9"),1,2); mk("C", self.clear,1,3)
        mk("4", lambda:self._a("4"),2,0); mk("5", lambda:self._a("5"),2,1); mk("6", lambda:self._a("6"),2,2); mk("÷", lambda:self._a("/"),2,3)
        mk("1", lambda:self._a("1"),3,0); mk("2", lambda:self._a("2"),3,1); mk("3", lambda:self._a("3"),3,2); mk("×", lambda:self._a("*"),3,3)
        mk("0", lambda:self._a("0"),4,0); mk(".", lambda:self._a("."),4,1); mk("=", self.equals,4,2); mk("−", lambda:self._a("-"),4,3)
        mk("(", lambda:self._a("("),5,0); mk(")", lambda:self._a(")"),5,1); mk("+", lambda:self._a("+"),5,2); mk("⌫", self.backspace,5,3)

    def _a(self, ch):
        self.var.set(self.var.get()+ch)

    def append_digit(self, d:int):
        self._a(str(max(0,min(9,int(d)))))

    def clear(self):
        self.var.set("")

    def backspace(self):
        self.var.set(self.var.get()[:-1])

    def equals(self):
        try:
            v = safe_eval(self.var.get())
            self.var.set(str(int(v)) if abs(v-int(v))<1e-10 else str(v))
        except:
            self.var.set("Error")

    def show(self):
        self.root.deiconify()

    def hide(self):
        self.root.withdraw()
