import sqlite3
import logging as log
import json
import os
from peers.Peer import Peer
from objects.Object import Object
from objects.Block import Block
from objects.UtxoSet import UtxoSet
from objects.Transaction import Transaction
from utils.json_builder import mk_canonical_json_str

DB_PATH = "persist"


class DbManager:
    def __init__(self):
        if not os.path.exists(DB_PATH):
            os.makedirs(DB_PATH)
        self._db_con = sqlite3.connect(f'{DB_PATH}/database.db', check_same_thread=False)
        self._db_cur = self._db_con.cursor()
        self._init_db()

    def close_db_connection(self):
        self._db_con.close()

    def add_peers(self, peers_to_add: list[Peer]):
        if peers_to_add:
            if len(peers_to_add) > 1:
                self._db_cur.executemany("INSERT OR IGNORE INTO known_peers VALUES(?, ?)",
                                         [p.to_tuple() for p in peers_to_add])
            else:
                self._db_cur.execute("INSERT OR IGNORE INTO known_peers VALUES(?, ?)", peers_to_add[0].to_tuple())

            self._db_con.commit()

            # TODO: Maybe fix this if we ever switch to a DBMS
            log.debug("Inserted new peers into DB")
            # if self._db_cur.rowcount > 0:
            #    log.debug(f"Discovered {self._db_cur.rowcount} new peers.")

    def remove_peer(self, peer: Peer):
        self._db_cur.execute("DELETE FROM known_peers WHERE ip_address = ?", (peer.host,))
        self._db_con.commit()

        # TODO: Maybe fix this if we ever switch to a DBMS
        log.debug(f"Removed peer {peer} from DB")
        # if self._db_cur.rowcount > 0:
        #    log.debug(f"Removed peer {peer} from list of known peers.")
        #    return
        # log.debug(f"Couldn't remove peer {peer} because they already were not in the list of known peers.")

    def get_peers(self) -> list[Peer]:
        result = self._db_cur.execute("SELECT * FROM known_peers")
        return [Peer(p[0], p[1]) for p in result.fetchall()]

    def get_random_peers(self, amount: int) -> list[Peer]:
        result = self._db_cur.execute("SELECT * FROM known_peers ORDER BY RANDOM() LIMIT ?", (amount,))
        return [Peer(p[0], p[1]) for p in result.fetchall()]

    def get_object(self, object_id: str) -> "Object|None":
        result = self._db_cur.execute("SELECT * FROM objects WHERE object_id = ?", (object_id,)).fetchone()

        if result:
            type = result[1]
            if type == "block":
                obj_result = self._db_cur.execute("SELECT * FROM blocks WHERE object_id = ?", (object_id,)).fetchone()
                obj_result = json.loads(obj_result[2])
                return Block.load_from_json(obj_result)
            elif type == "transaction":
                obj_result = self._db_cur.execute("SELECT * FROM transactions WHERE object_id = ?",
                                                  (object_id,)).fetchone()
                obj_result = json.loads(obj_result[2])
                return Transaction.load_from_json(obj_result)

        return None

    def add_object(self, obj: Object) -> bool:
        has_been_added = self._check_if_obj_in_db(obj.object_id)

        if not has_been_added:
            self._db_cur.execute("INSERT OR IGNORE INTO objects VALUES(?, ?)", (obj.object_id, obj.type))

            # TODO: Maybe fix this if we ever switch to a DBMS
            # has_been_added = self._db_cur.rowcount

            if obj.type == "block":
                self._db_cur.execute("INSERT OR IGNORE INTO blocks VALUES(NULL, ?, ?)",
                                     (obj.object_id, mk_canonical_json_str(Block.to_json(obj))))  # type: ignore
            elif obj.type == "transaction":
                self._db_cur.execute("INSERT OR IGNORE INTO transactions VALUES (NULL, ?, ?)",
                                     (obj.object_id, mk_canonical_json_str(Transaction.to_json(obj))))  # type: ignore

            self._db_con.commit()
        else:
            log.info(f"Received Object ID {obj.object_id} had already been stored in DB")

        return not has_been_added

    def get_utxo_set(self, set_id: str) -> "UtxoSet|None":
        result = self._db_cur.execute("SELECT tx_obj_str FROM utxo_sets WHERE set_id = ?",
                                      (set_id,)).fetchone()
        return result[0] if result else None

    def add_utxo_set(self, obj: UtxoSet) -> bool:
        self._db_cur.execute("INSERT OR IGNORE INTO utxo_sets VALUES(?, ?)", (obj.set_id, obj.balances))
        self._db_con.commit()

    def get_tx_obj(self, object_id: str) -> "str | None":
        result = self._db_cur.execute("SELECT tx_obj_str FROM transactions WHERE object_id = ?",
                                      (object_id,)).fetchone()
        return result[0] if result else None

    def _check_if_obj_in_db(self, object_id) -> bool:
        result = self._db_cur.execute("SELECT EXISTS(SELECT 1 FROM objects WHERE object_id = ?)", (object_id,))
        return bool(result.fetchone()[0])

    def _init_db(self):
        res = self._db_cur.execute("SELECT name FROM sqlite_master")

        if not res.fetchone():
            self._db_cur.executescript("""
                BEGIN;
                CREATE TABLE known_peers(ip_address PRIMARY KEY, port);
                CREATE TABLE objects(object_id PRIMARY KEY, type);
                CREATE TABLE blocks(id INTEGER PRIMARY KEY, object_id, block_obj_str, FOREIGN KEY (object_id) REFERENCES objects(object_id));
                CREATE TABLE transactions(id INTEGER PRIMARY KEY, object_id, tx_obj_str, FOREIGN KEY (object_id) REFERENCES objects(object_id));
                CREATE TABLE utxo_sets(id INTEGER PRIMARY KEY , set_id, utxo_set_sting);
                COMMIT;
            """)
            self._db_con.commit()
