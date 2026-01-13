import * as SQLite from 'expo-sqlite';

export const initDatabase = async () => {
  try {
    const db = await SQLite.openDatabaseAsync('preptracker.db');

    // Create clients table
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // Create orders table
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        reference TEXT NOT NULL,
        status TEXT DEFAULT 'todo',
        priority INTEGER DEFAULT 0,
        due_date DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id)
      );
    `);

    // Create daily_notes table
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS daily_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        client_id INTEGER,
        content TEXT NOT NULL,
        note_date DATE DEFAULT (date('now')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (client_id) REFERENCES clients(id)
      );
    `);

    console.log('Database initialized successfully');
    return db;
  } catch (error) {
    console.error('Error initializing database:', error);
    throw error;
  }
};

export const getDatabase = async () => {
  return await SQLite.openDatabaseAsync('preptracker.db');
};
