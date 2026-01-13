import { getDatabase } from './schema';

export type OrderStatus = 'todo' | 'in_progress' | 'done' | 'problem';

export interface Client {
  id?: number;
  name: string;
  code?: string;
  notes?: string;
  created_at?: string;
}

export interface Order {
  id?: number;
  client_id: number;
  reference: string;
  status: OrderStatus;
  priority: number;
  due_date?: string;
  created_at?: string;
  updated_at?: string;
  client_name?: string;
  client_code?: string;
}

export interface DailyNote {
  id?: number;
  order_id?: number;
  client_id?: number;
  content: string;
  note_date?: string;
  created_at?: string;
}

// ============ CLIENTS ============

export const getAllClients = async (): Promise<Client[]> => {
  const db = await getDatabase();
  const result = await db.getAllAsync<Client>('SELECT * FROM clients ORDER BY name ASC');
  return result;
};

export const getClientById = async (id: number): Promise<Client | null> => {
  const db = await getDatabase();
  const result = await db.getFirstAsync<Client>('SELECT * FROM clients WHERE id = ?', [id]);
  return result || null;
};

export const createClient = async (client: Omit<Client, 'id' | 'created_at'>): Promise<number> => {
  const db = await getDatabase();
  const result = await db.runAsync(
    'INSERT INTO clients (name, code, notes) VALUES (?, ?, ?)',
    [client.name, client.code || null, client.notes || null]
  );
  return result.lastInsertRowId;
};

export const updateClient = async (id: number, client: Partial<Client>): Promise<void> => {
  const db = await getDatabase();
  const fields = [];
  const values = [];

  if (client.name !== undefined) {
    fields.push('name = ?');
    values.push(client.name);
  }
  if (client.code !== undefined) {
    fields.push('code = ?');
    values.push(client.code);
  }
  if (client.notes !== undefined) {
    fields.push('notes = ?');
    values.push(client.notes);
  }

  if (fields.length > 0) {
    values.push(id);
    await db.runAsync(
      `UPDATE clients SET ${fields.join(', ')} WHERE id = ?`,
      values
    );
  }
};

export const deleteClient = async (id: number): Promise<void> => {
  const db = await getDatabase();
  await db.runAsync('DELETE FROM clients WHERE id = ?', [id]);
};

// ============ ORDERS ============

export const getAllOrders = async (): Promise<Order[]> => {
  const db = await getDatabase();
  const result = await db.getAllAsync<Order>(
    `SELECT orders.*, clients.name as client_name, clients.code as client_code
     FROM orders
     LEFT JOIN clients ON orders.client_id = clients.id
     ORDER BY orders.created_at DESC`
  );
  return result;
};

export const getOrdersByStatus = async (status: OrderStatus): Promise<Order[]> => {
  const db = await getDatabase();
  const result = await db.getAllAsync<Order>(
    `SELECT orders.*, clients.name as client_name, clients.code as client_code
     FROM orders
     LEFT JOIN clients ON orders.client_id = clients.id
     WHERE orders.status = ?
     ORDER BY orders.priority DESC, orders.due_date ASC`,
    [status]
  );
  return result;
};

export const getOrdersByClient = async (clientId: number): Promise<Order[]> => {
  const db = await getDatabase();
  const result = await db.getAllAsync<Order>(
    `SELECT orders.*, clients.name as client_name, clients.code as client_code
     FROM orders
     LEFT JOIN clients ON orders.client_id = clients.id
     WHERE orders.client_id = ?
     ORDER BY orders.created_at DESC`,
    [clientId]
  );
  return result;
};

export const getOrdersByDate = async (date: string): Promise<Order[]> => {
  const db = await getDatabase();
  const result = await db.getAllAsync<Order>(
    `SELECT orders.*, clients.name as client_name, clients.code as client_code
     FROM orders
     LEFT JOIN clients ON orders.client_id = clients.id
     WHERE date(orders.due_date) = date(?)
     ORDER BY orders.priority DESC`,
    [date]
  );
  return result;
};

export const getOrderById = async (id: number): Promise<Order | null> => {
  const db = await getDatabase();
  const result = await db.getFirstAsync<Order>(
    `SELECT orders.*, clients.name as client_name, clients.code as client_code
     FROM orders
     LEFT JOIN clients ON orders.client_id = clients.id
     WHERE orders.id = ?`,
    [id]
  );
  return result || null;
};

export const createOrder = async (order: Omit<Order, 'id' | 'created_at' | 'updated_at'>): Promise<number> => {
  const db = await getDatabase();
  const result = await db.runAsync(
    'INSERT INTO orders (client_id, reference, status, priority, due_date) VALUES (?, ?, ?, ?, ?)',
    [order.client_id, order.reference, order.status, order.priority, order.due_date || null]
  );
  return result.lastInsertRowId;
};

export const updateOrder = async (id: number, order: Partial<Order>): Promise<void> => {
  const db = await getDatabase();
  const fields = ['updated_at = CURRENT_TIMESTAMP'];
  const values = [];

  if (order.client_id !== undefined) {
    fields.push('client_id = ?');
    values.push(order.client_id);
  }
  if (order.reference !== undefined) {
    fields.push('reference = ?');
    values.push(order.reference);
  }
  if (order.status !== undefined) {
    fields.push('status = ?');
    values.push(order.status);
  }
  if (order.priority !== undefined) {
    fields.push('priority = ?');
    values.push(order.priority);
  }
  if (order.due_date !== undefined) {
    fields.push('due_date = ?');
    values.push(order.due_date);
  }

  values.push(id);
  await db.runAsync(
    `UPDATE orders SET ${fields.join(', ')} WHERE id = ?`,
    values
  );
};

export const deleteOrder = async (id: number): Promise<void> => {
  const db = await getDatabase();
  await db.runAsync('DELETE FROM orders WHERE id = ?', [id]);
};

export const searchOrders = async (query: string): Promise<Order[]> => {
  const db = await getDatabase();
  const searchTerm = `%${query}%`;
  const result = await db.getAllAsync<Order>(
    `SELECT orders.*, clients.name as client_name, clients.code as client_code
     FROM orders
     LEFT JOIN clients ON orders.client_id = clients.id
     WHERE orders.reference LIKE ? OR clients.name LIKE ? OR clients.code LIKE ?
     ORDER BY orders.created_at DESC`,
    [searchTerm, searchTerm, searchTerm]
  );
  return result;
};

// ============ DAILY NOTES ============

export const getNotesForOrder = async (orderId: number): Promise<DailyNote[]> => {
  const db = await getDatabase();
  const result = await db.getAllAsync<DailyNote>(
    'SELECT * FROM daily_notes WHERE order_id = ? ORDER BY created_at DESC',
    [orderId]
  );
  return result;
};

export const createNote = async (note: Omit<DailyNote, 'id' | 'created_at'>): Promise<number> => {
  const db = await getDatabase();
  const result = await db.runAsync(
    'INSERT INTO daily_notes (order_id, client_id, content, note_date) VALUES (?, ?, ?, ?)',
    [note.order_id || null, note.client_id || null, note.content, note.note_date || null]
  );
  return result.lastInsertRowId;
};

export const deleteNote = async (id: number): Promise<void> => {
  const db = await getDatabase();
  await db.runAsync('DELETE FROM daily_notes WHERE id = ?', [id]);
};

// ============ STATS ============

export interface DailyStats {
  todo: number;
  in_progress: number;
  done: number;
  problem: number;
  urgent: number;
}

export const getDailyStats = async (date?: string): Promise<DailyStats> => {
  const db = await getDatabase();
  const targetDate = date || new Date().toISOString().split('T')[0];

  const stats: DailyStats = {
    todo: 0,
    in_progress: 0,
    done: 0,
    problem: 0,
    urgent: 0,
  };

  const todoCount = await db.getFirstAsync<{ count: number }>(
    'SELECT COUNT(*) as count FROM orders WHERE status = ? AND (due_date IS NULL OR date(due_date) <= date(?))',
    ['todo', targetDate]
  );
  stats.todo = todoCount?.count || 0;

  const inProgressCount = await db.getFirstAsync<{ count: number }>(
    'SELECT COUNT(*) as count FROM orders WHERE status = ?',
    ['in_progress']
  );
  stats.in_progress = inProgressCount?.count || 0;

  const doneCount = await db.getFirstAsync<{ count: number }>(
    'SELECT COUNT(*) as count FROM orders WHERE status = ? AND date(updated_at) = date(?)',
    ['done', targetDate]
  );
  stats.done = doneCount?.count || 0;

  const problemCount = await db.getFirstAsync<{ count: number }>(
    'SELECT COUNT(*) as count FROM orders WHERE status = ?',
    ['problem']
  );
  stats.problem = problemCount?.count || 0;

  const urgentCount = await db.getFirstAsync<{ count: number }>(
    'SELECT COUNT(*) as count FROM orders WHERE priority = 1 AND status != ?',
    ['done']
  );
  stats.urgent = urgentCount?.count || 0;

  return stats;
};
