use dbconnector::{DBConnector, Entry};
use std::sync::mpsc::{channel, Receiver, Sender};


pub struct HyperDBDriver {
    db: DBConnector,
    height: i64,
}

impl HyperDBDriver {
    pub fn new(db: DBConnector) -> HyperDBDriver {
        HyperDBDriver {
            db,
            height: 0,
        }
    }

    pub fn get_height(&self) -> i64 {
        self.height
    }

    pub fn get_entries(&mut self) -> Vec<Entry> {
        return self.db.get_entries();
    }

    pub fn get_entry(&mut self, id: i32) -> Result<Entry, String> {
        return self.db.get_entry(id);
    }

    pub fn insert_entry(&mut self, entry: &Entry) -> Result<(), String> {
        return self.db.insert_entry(entry);
    }

}