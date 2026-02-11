class Validators:
    """统一输入验证器类"""
    
    @staticmethod
    def positive_int(P):
        """验证正整数"""
        if not P.strip():
            return True
        try:
            return int(P) > 0
        except ValueError:
            return False
    
    @staticmethod
    def register_entry(entry, var=None):
        """一键注册验证器 + 失焦处理"""
        entry.configure(validate="key", 
                       validatecommand=(entry.register(Validators.positive_int), '%P'))
        if var:
            entry.bind("<FocusOut>", lambda e: var.set(max(1, var.get() or 100)))
