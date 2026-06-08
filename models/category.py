from .database import Database

class Category:
    @staticmethod
    def create(name, cat_type):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO categories (name, type) VALUES (?, ?)", (name, cat_type))
            return cursor.lastrowid

    @staticmethod
    def get_all(type_filter=None):
        with Database.get_connection() as conn:
            # Ép cấu trúc Row để có thể truy xuất dữ liệu theo dạng dict: cat['type'], cat['id']
            conn.row_factory = lambda cursor, row: {
                "id": row[0],
                "name": row[1],
                "type": row[2]
            }
            cursor = conn.cursor()
            
            if type_filter:
                cursor.execute("SELECT id, name, type FROM categories WHERE type = ? ORDER BY name", (type_filter,))
            else:
                cursor.execute("SELECT id, name, type FROM categories ORDER BY name")
                
            return cursor.fetchall()

    @staticmethod
    def update(cat_id, name=None, cat_type=None):
        updates = []
        values = []
        if name is not None:
            updates.append("name = ?")
            values.append(name)
        if cat_type is not None:
            updates.append("type = ?")
            values.append(cat_type)
        if updates:
            values.append(cat_id)
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE categories SET {', '.join(updates)} WHERE id = ?", values)
                return cursor.rowcount > 0
        return False

    @staticmethod
    def delete(cat_id):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
            return cursor.rowcount > 0