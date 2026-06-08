import tkinter as tk
from tkinter import ttk, messagebox
from models.category import Category

class CategoryManager:
    def __init__(self, parent, refresh_callback=None):
        self.parent = parent
        self.refresh_callback = refresh_callback
        self.window = tk.Toplevel(parent)
        self.window.title("Quản lý danh mục giao dịch")
        self.window.geometry("600x500")
        self.window.transient(parent)
        self.window.grab_set()
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab Thu
        self.income_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.income_frame, text="Danh mục Thu")
        self.create_category_list(self.income_frame, "Thu")

        # Tab Chi
        self.expense_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.expense_frame, text="Danh mục Chi")
        self.create_category_list(self.expense_frame, "Chi")

    def create_category_list(self, parent, cat_type):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        tree = ttk.Treeview(main_frame, columns=("ID", "Tên"), show="headings", height=12)
        tree.heading("ID", text="ID")
        tree.heading("Tên", text="Tên danh mục")
        tree.column("ID", width=50, anchor="center")
        tree.column("Tên", width=400, anchor="w")
        tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        form_frame = ttk.Frame(parent)
        form_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(form_frame, text="Tên danh mục mới:").pack(side="left", padx=5)
        entry = ttk.Entry(form_frame, width=40)
        entry.pack(side="left", padx=5, fill="x", expand=True)

        def add():
            name = entry.get().strip()
            if name:
                try:
                    Category.create(name, cat_type)
                    self.load_data()
                    entry.delete(0, tk.END)
                    if self.refresh_callback:
                        self.refresh_callback()
                except Exception as e:
                    messagebox.showerror("Lỗi", str(e))
            else:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên danh mục")

        ttk.Button(form_frame, text="Thêm", command=add).pack(side="left", padx=5)

        def delete():
            selected = tree.selection()
            if selected:
                cat_id = tree.item(selected[0], "values")[0]
                if messagebox.askyesno("Xác nhận", "Xóa danh mục này? Các giao dịch đã có danh mục này sẽ không bị ảnh hưởng."):
                    Category.delete(cat_id)
                    self.load_data()
                    if self.refresh_callback:
                        self.refresh_callback()
            else:
                messagebox.showwarning("Cảnh báo", "Chọn danh mục cần xóa")

        ttk.Button(form_frame, text="Xóa", command=delete).pack(side="left", padx=5)

        if not hasattr(self, 'trees'):
            self.trees = {}
        self.trees[cat_type] = tree

    def load_data(self):
        if not hasattr(self, 'trees'):
            return
        for tree in self.trees.values():
            for item in tree.get_children():
                tree.delete(item)
        categories = Category.get_all()
        for cat in categories:
            tree = self.trees.get(cat['type'])
            if tree:
                tree.insert("", "end", values=(cat['id'], cat['name']))