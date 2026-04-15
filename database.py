import pandas as pd
import sqlite3
from pathlib import Path

DB_PATH = 'bursaspor_performans.db' # Veritabanı adı güncellendi

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.init_db()
        self._migrate()

    def get_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS camps (
                camp_id    INTEGER PRIMARY KEY,
                age_group  TEXT NOT NULL,
                camp_name  TEXT NOT NULL,
                start_date TEXT,
                end_date   TEXT,
                location   TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(camp_id, age_group)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS players (
                player_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                age_group  TEXT NOT NULL,
                photo_url  TEXT,
                club_logo_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, age_group)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS performance_data (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name    TEXT NOT NULL,
                age_group      TEXT NOT NULL,
                camp_id        INTEGER NOT NULL,
                tarih          TEXT NOT NULL,
                minutes        REAL DEFAULT 0,
                total_distance REAL DEFAULT 0,
                metrage        REAL DEFAULT 0,
                dist_20_25     REAL DEFAULT 0,
                dist_25_plus   REAL DEFAULT 0,
                dist_acc_3     REAL,
                dist_dec_3     REAL,
                n_20_25        REAL,
                n_25_plus      REAL,
                smax_kmh       REAL DEFAULT 0,
                player_load    REAL DEFAULT 0,
                amp            REAL DEFAULT 0,
                tip            TEXT,
                data_type      TEXT,
                has_acc_dec    INTEGER DEFAULT 0,
                has_n_counts   INTEGER DEFAULT 0,
                created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_name, camp_id, tarih)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                age_group   TEXT NOT NULL,
                camp_id     INTEGER NOT NULL,
                tarih       TEXT NOT NULL,
                status      TEXT NOT NULL,
                reason      TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_name, camp_id, tarih)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                action     TEXT NOT NULL,
                detail     TEXT,
                user       TEXT DEFAULT 'system',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS performance_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                age_group TEXT NOT NULL,
                tarih TEXT NOT NULL,
                bw_kg REAL,
                height_cm REAL,
                cmj_jump_cm REAL,
                slj_jump_cm REAL,
                slj_jump_l_cm REAL,
                slj_jump_r_cm REAL,
                slj_asym_pct TEXT,
                sj_jump_cm REAL,
                nordic_l_n REAL,
                nordic_r_n REAL,
                nordic_imbalance_pct REAL,
                pull_l_n REAL,
                pull_r_n REAL,
                pull_imbalance_pct REAL,
                squeeze_l_n REAL,
                squeeze_r_n REAL,
                squeeze_imbalance_pct REAL,
                knee_ext_l_n REAL,
                knee_ext_r_n REAL,
                knee_ext_imbalance_pct REAL,
                sprint_10m REAL,
                sprint_20m REAL,
                sprint_30m REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_name, tarih)
            )
        ''')
        conn.commit()

    def _migrate(self):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("PRAGMA table_info(performance_data)")
        existing_perf = {row[1] for row in c.fetchall()}
        
        c.execute("PRAGMA table_info(players)")
        existing_players = {row[1] for row in c.fetchall()}

        migrations = [
            ("has_acc_dec",  "ALTER TABLE performance_data ADD COLUMN has_acc_dec INTEGER DEFAULT 0", existing_perf),
            ("has_n_counts", "ALTER TABLE performance_data ADD COLUMN has_n_counts INTEGER DEFAULT 0", existing_perf),
            ("dist_acc_3",   "ALTER TABLE performance_data ADD COLUMN dist_acc_3 REAL", existing_perf),
            ("dist_dec_3",   "ALTER TABLE performance_data ADD COLUMN dist_dec_3 REAL", existing_perf),
            ("n_20_25",      "ALTER TABLE performance_data ADD COLUMN n_20_25 REAL", existing_perf),
            ("n_25_plus",    "ALTER TABLE performance_data ADD COLUMN n_25_plus REAL", existing_perf),
            ("data_type",    "ALTER TABLE performance_data ADD COLUMN data_type TEXT", existing_perf),
            ("photo_url",    "ALTER TABLE players ADD COLUMN photo_url TEXT", existing_players),
            ("club_logo_url","ALTER TABLE players ADD COLUMN club_logo_url TEXT", existing_players),
        ]
        for col_name, sql, table_cols in migrations:
            if col_name not in table_cols:
                try:
                    c.execute(sql)
                except Exception:
                    pass
        try:
            c.execute("UPDATE performance_data SET has_acc_dec = 1 WHERE dist_acc_3 IS NOT NULL AND dist_acc_3 != 0 AND has_acc_dec = 0")
            c.execute("UPDATE performance_data SET has_n_counts = 1 WHERE n_20_25 IS NOT NULL AND n_20_25 != 0 AND has_n_counts = 0")
        except Exception:
            pass
        conn.commit()

    def excel_to_db(self, file_path, age_group):
        try:
            df = pd.read_excel(file_path, sheet_name='Training_Match_Data')
            df.columns = [str(c).strip() for c in df.columns]
            hafta_info = self._extract_camp_info(file_path, age_group)
            df_norm   = self._normalize_data(df, age_group, hafta_info)
            conn = self.get_connection()
            c    = conn.cursor()
            dates = pd.to_datetime(df_norm['tarih'])
            c.execute('INSERT OR REPLACE INTO camps (camp_id, age_group, camp_name, start_date, end_date) VALUES (?,?,?,?,?)',
                (hafta_info['camp_id'], age_group, hafta_info['camp_name'],
                 dates.min().strftime('%Y-%m-%d'), dates.max().strftime('%Y-%m-%d')))
            for pname in df_norm['player_name'].unique():
                c.execute('INSERT OR IGNORE INTO players (name, age_group) VALUES (?,?)', (pname, age_group))
            inserted = 0
            for _, row in df_norm.iterrows():
                try:
                    c.execute('''INSERT OR REPLACE INTO performance_data
                        (player_name, age_group, camp_id, tarih,
                         minutes, total_distance, metrage, dist_20_25, dist_25_plus,
                         dist_acc_3, dist_dec_3, n_20_25, n_25_plus,
                         smax_kmh, player_load, amp, tip, data_type, has_acc_dec, has_n_counts)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                        (row['player_name'], row['age_group'], row['camp_id'], row['tarih'],
                         row['minutes'], row['total_distance'], row['metrage'],
                         row['dist_20_25'], row['dist_25_plus'],
                         row.get('dist_acc_3'), row.get('dist_dec_3'),
                         row.get('n_20_25'), row.get('n_25_plus'),
                         row['smax_kmh'], row['player_load'], row['amp'],
                         row['tip'], row['data_type'],
                         int(row['has_acc_dec']), int(row['has_n_counts'])))
                    inserted += 1
                except Exception:
                    pass
            self._log_action('excel_import', f"{age_group} / {hafta_info['camp_name']} — {inserted} satır")
            conn.commit()
            return {'status': 'success',
                    'message': f"✅ {inserted} satır yüklendi — {age_group} / {hafta_info['camp_name']}",
                    'records': inserted,
                    'has_acc_dec': bool(df_norm['has_acc_dec'].iloc[0]),
                    'has_n_counts': bool(df_norm['has_n_counts'].iloc[0])}
        except Exception as e:
            return {'status': 'error', 'message': f"❌ Hata: {str(e)}"}

    def test_excel_to_db(self, file_path, age_group, test_date):
        try:
            df = pd.read_excel(file_path)
            df.columns = [str(c).strip() for c in df.columns]
            
            col_map = {
                'Name': 'player_name',
                'BW (kg)': 'bw_kg',
                'Height': 'height_cm',
                'CMJ Jump Height (Imp-Mom) [cm]': 'cmj_jump_cm',
                'SLJ Jump Height (Imp-Mom) [cm]': 'slj_jump_cm',
                'SLJ Jump Height (Imp-Mom) [cm] (L)': 'slj_jump_l_cm',
                'SLJ Jump Height (Imp-Mom) [cm] (R)': 'slj_jump_r_cm',
                'SLJ Jump Height (Imp-Mom) [cm] (Asym)(%)': 'slj_asym_pct',
                'SJ Jump Height (Imp-Mom) [cm]': 'sj_jump_cm',
                'Nordic L Max Force (N)': 'nordic_l_n',
                'Nordic R Max Force (N)': 'nordic_r_n',
                'Nordic Max Imbalance (%)': 'nordic_imbalance_pct',
                'Pull L Max Force (N)': 'pull_l_n',
                'Pull R Max Force (N)': 'pull_r_n',
                'Pull Max Imbalance': 'pull_imbalance_pct',
                'Squeeze L Max Force (N)': 'squeeze_l_n',
                'Squeeze R Max Force (N)': 'squeeze_r_n',
                'Squeeze Max Imbalance': 'squeeze_imbalance_pct',
                'Knee Extension L Max Force (N)': 'knee_ext_l_n',
                'Knee Extension R Max Force (N)': 'knee_ext_r_n',
                'Knee Extension Max Imbalance': 'knee_ext_imbalance_pct',
                '10m Sprint': 'sprint_10m',
                '20m Sprint': 'sprint_20m',
                '30m Sprint': 'sprint_30m'
            }

            conn = self.get_connection()
            c = conn.cursor()
            inserted = 0

            for _, row in df.iterrows():
                if pd.isna(row.get('Name')) or str(row.get('Name')).strip() == '':
                    continue
                
                p_name = str(row['Name']).strip()
                
                row_date = test_date
                if 'Date' in df.columns and not pd.isna(row['Date']):
                    try:
                        row_date = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
                    except:
                        pass 

                c.execute('INSERT OR IGNORE INTO players (name, age_group) VALUES (?,?)', (p_name, age_group))

                db_values = {}
                for excel_col, db_col in col_map.items():
                    if excel_col in df.columns and not pd.isna(row[excel_col]):
                        db_values[db_col] = row[excel_col]
                    else:
                        db_values[db_col] = None

                try:
                    c.execute('''
                        INSERT OR REPLACE INTO performance_tests (
                            player_name, age_group, tarih, bw_kg, height_cm, cmj_jump_cm, slj_jump_cm, 
                            slj_jump_l_cm, slj_jump_r_cm, slj_asym_pct, sj_jump_cm, 
                            nordic_l_n, nordic_r_n, nordic_imbalance_pct, 
                            pull_l_n, pull_r_n, pull_imbalance_pct, 
                            squeeze_l_n, squeeze_r_n, squeeze_imbalance_pct, 
                            knee_ext_l_n, knee_ext_r_n, knee_ext_imbalance_pct, 
                            sprint_10m, sprint_20m, sprint_30m
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        p_name, age_group, row_date, 
                        db_values['bw_kg'], db_values['height_cm'], db_values['cmj_jump_cm'], db_values['slj_jump_cm'],
                        db_values['slj_jump_l_cm'], db_values['slj_jump_r_cm'], 
                        str(db_values['slj_asym_pct']) if db_values['slj_asym_pct'] else None, db_values['sj_jump_cm'],
                        db_values['nordic_l_n'], db_values['nordic_r_n'], db_values['nordic_imbalance_pct'],
                        db_values['pull_l_n'], db_values['pull_r_n'], db_values['pull_imbalance_pct'],
                        db_values['squeeze_l_n'], db_values['squeeze_r_n'], db_values['squeeze_imbalance_pct'],
                        db_values['knee_ext_l_n'], db_values['knee_ext_r_n'], db_values['knee_ext_imbalance_pct'],
                        db_values['sprint_10m'], db_values['sprint_20m'], db_values['sprint_30m']
                    ))
                    inserted += 1
                except Exception as insert_e:
                    print(f"Kuvvet Testi satırı eklenirken hata: {insert_e}")
                    pass

            self._log_action('test_data_import', f"{age_group} Test Verisi — {inserted} satır")
            conn.commit()
            return {'status': 'success', 'message': f"✅ {inserted} test kaydı {age_group} grubuna başarıyla yüklendi!"}
            
        except Exception as e:
            return {'status': 'error', 'message': f"❌ Hata: {str(e)}"}

    def get_test_data(self, age_group=None, player_name=None):
        query = "SELECT * FROM performance_tests WHERE 1=1"
        params = []
        if age_group:
            query += " AND age_group = ?"
            params.append(age_group)
        if player_name:
            query += " AND player_name = ?"
            params.append(player_name)
        
        query += " ORDER BY tarih DESC"
        return self._read(query, tuple(params))

    def _extract_camp_info(self, file_path, age_group):
        name = getattr(file_path, 'name', str(file_path))
        stem = Path(name).stem
        parts = stem.split('_')
        hafta_name = '_'.join(parts[1:]) if len(parts) > 1 else stem
        hafta_id   = abs(hash(stem)) % 100000
        return {'camp_id': hafta_id, 'camp_name': hafta_name, 'start_date': None, 'end_date': None}

    def _normalize_data(self, df, age_group, hafta_info):
        d = df.copy()
        d['tarih_dt'] = pd.to_datetime(d['Tarih'], dayfirst=True, errors='coerce')
        has_acc_dec  = 'Dist Acc>3' in d.columns
        has_n_counts = ('N 20-25' in d.columns or 'N > 25' in d.columns)
        
        def to_num(col):
            if col in d.columns:
                return pd.to_numeric(d[col].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
            return pd.Series([0.0]*len(d))
            
        def to_num_opt(col):
            if col in d.columns:
                return pd.to_numeric(d[col].astype(str).str.replace(',','.'), errors='coerce')
            return pd.Series([None]*len(d))
            
        tip_col = None
        for col in d.columns:
            if str(col).upper().strip() in ['TIP', 'TİP', 'SESSION', 'SEANS', 'SEANS TİPİ', 'ACTIVITY']:
                tip_col = col
                break
                
        if tip_col:
            raw_tip = d[tip_col].astype(str).str.upper().str.strip()
        else:
            raw_tip = pd.Series(['TRAINING']*len(d))
            
        def parse_tip(val):
            if any(k in val for k in ['MATCH', 'MAÇ', 'MAC', 'GAME', 'MÜSABAKA']):
                return 'MATCH'
            return 'TRAINING'
            
        final_tip = raw_tip.apply(parse_tip)
        
        name_col = 'Name' if 'Name' in d.columns else d.columns[0]
        smax     = to_num('SMax (kmh)') if 'SMax (kmh)' in d.columns else to_num('S.Max (kmh)')
        
        result = pd.DataFrame({
            'player_name': d[name_col].astype(str).str.strip(),
            'age_group':   age_group,
            'camp_id':     hafta_info['camp_id'],
            'tarih':       d['tarih_dt'].dt.strftime('%Y-%m-%d'),
            'minutes':     to_num('Minutes'),
            'total_distance': to_num('Total Distance'),
            'metrage':     to_num('Metrage'),
            'dist_20_25':  to_num('Dist 20-25'),
            'dist_25_plus': to_num('Dist > 25'),
            'dist_acc_3':  to_num_opt('Dist Acc>3'),
            'dist_dec_3':  to_num_opt('Dist Dec<-3'),
            'n_20_25':     to_num_opt('N 20-25'),
            'n_25_plus':   to_num_opt('N > 25'),
            'smax_kmh':    smax,
            'player_load': to_num('Player Load'),
            'amp':         to_num('AMP'),
            'tip':         final_tip,          
            'data_type':   final_tip,          
            'has_acc_dec': has_acc_dec,
            'has_n_counts': has_n_counts,
        })
        return result.dropna(subset=['tarih'])

    def _read(self, query, params=()):
        conn = self.get_connection()
        df   = pd.read_sql_query(query, conn, params=params)
        if 'tarih' in df.columns:
            df['tarih'] = pd.to_datetime(df['tarih'])
        return df

    def _log_action(self, action: str, detail: str = '', user: str = 'system'):
        try:
            conn = self.get_connection()
            conn.execute('INSERT INTO audit_log (action, detail, user) VALUES (?,?,?)', (action, detail, user))
            conn.commit()
        except Exception:
            pass

    def get_audit_log(self, limit: int = 10) -> pd.DataFrame:
        try:
            df = self._read('SELECT id, action, detail, user, created_at FROM audit_log ORDER BY created_at DESC LIMIT ?', (limit,))
            return df
        except Exception:
            return pd.DataFrame(columns=['id', 'action', 'detail', 'user', 'created_at'])

    def get_all_data(self):
        return self._read('SELECT * FROM performance_data ORDER BY tarih DESC')

    def get_data_by_age_group(self, age_group):
        return self._read('SELECT * FROM performance_data WHERE age_group=? ORDER BY tarih DESC', (age_group,))

    def get_data_by_camp(self, camp_id):
        return self._read('SELECT * FROM performance_data WHERE camp_id=? ORDER BY tarih', (camp_id,))

    def get_data_by_player(self, player_name):
        return self._read('SELECT * FROM performance_data WHERE player_name=? ORDER BY tarih', (player_name,))

    def get_camps(self, age_group=None):
        if age_group:
            return self._read('SELECT DISTINCT camp_id, camp_name, age_group, start_date, end_date FROM camps WHERE age_group=? ORDER BY start_date DESC', (age_group,))
        return self._read('SELECT DISTINCT camp_id, camp_name, age_group, start_date, end_date FROM camps ORDER BY age_group, start_date DESC')

    def update_player_images(self, player_name, photo_url, club_logo_url):
        conn = self.get_connection()
        conn.execute('UPDATE players SET photo_url=?, club_logo_url=? WHERE name=?', (photo_url, club_logo_url, player_name))
        conn.commit()

    def get_player_info(self, player_name):
        df = self._read('SELECT * FROM players WHERE name=?', (player_name,))
        if not df.empty:
            return df.iloc[0].to_dict()
        return {}

    def get_players_with_info(self, age_group):
        df = self._read('SELECT * FROM players WHERE age_group=? ORDER BY name', (age_group,))
        return df.to_dict('records') if not df.empty else []

    def get_players(self, age_group=None):
        if age_group:
            df = self._read('SELECT DISTINCT name FROM players WHERE age_group=? ORDER BY name', (age_group,))
        else:
            df = self._read('SELECT DISTINCT name FROM players ORDER BY name')
        return df['name'].tolist() if not df.empty else []

    def camp_has_acc_dec(self, camp_id):
        try:
            df = self._read('SELECT has_acc_dec FROM performance_data WHERE camp_id=? LIMIT 1', (camp_id,))
            if not df.empty and df['has_acc_dec'].iloc[0]: return True
            df2 = self._read('SELECT dist_acc_3 FROM performance_data WHERE camp_id=? AND dist_acc_3 IS NOT NULL AND dist_acc_3 != 0 LIMIT 1', (camp_id,))
            return not df2.empty
        except Exception:
            return False

    def camp_has_n_counts(self, camp_id):
        try:
            df = self._read('SELECT has_n_counts FROM performance_data WHERE camp_id=? LIMIT 1', (camp_id,))
            if not df.empty and df['has_n_counts'].iloc[0]: return True
            df2 = self._read('SELECT n_20_25 FROM performance_data WHERE camp_id=? AND n_20_25 IS NOT NULL AND n_20_25 != 0 LIMIT 1', (camp_id,))
            return not df2.empty
        except Exception:
            return False

    def delete_camp_data(self, camp_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM performance_data WHERE camp_id = ?", (camp_id,))
                conn.execute("DELETE FROM camps WHERE camp_id = ?", (camp_id,))
            self._log_action("delete_camp", f"Hafta ID {camp_id} sistemden silindi.")
            return True
        except Exception as e:
            print(f"Silme hatası: {e}")
            return False

    def delete_age_group_data(self, age_group):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM performance_data WHERE age_group = ?", (age_group,))
                conn.execute("DELETE FROM camps WHERE age_group = ?", (age_group,))
            self._log_action("delete_age_group", f"{age_group} tüm verileri silindi.")
            return True
        except Exception as e:
            print(f"Silme hatası: {e}")
            return False

db_manager = DatabaseManager()