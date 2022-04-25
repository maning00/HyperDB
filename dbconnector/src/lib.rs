use postgres::{Client, NoTls};
use tracing::{debug, error, info, warn};

#[derive(Debug)]
pub struct Entry {
    id: i32,
    name: String,
    experiment_time: i32,
    author: String,
    email: String,
    institution: String,
    environment: String,
    parameters: String,
    details: String,
    attachment: String,
    hash: String,
    offset: i32,
    timestamp: i32,
}

pub struct DBConnector {
    client: Client,
    user: String,
}

impl DBConnector {
    pub fn new(url: &str) -> DBConnector {
        let client = Client::connect(url, NoTls).unwrap();
        DBConnector { client, user: "".to_string() }
    }

    pub fn get_entries(&mut self) -> Vec<Entry> {
        let mut entries = Vec::new();
        let res = self.client.query("SELECT * FROM ustb", &[]);
        match res {
            Ok(rows) => {
                for row in rows.iter() {
                    let id: i32 = row.get(0);
                    let name: String = row.get(1);
                    let experiment_time: i32 = row.get(2);
                    let author: String = row.get(3);
                    let email: String = row.get(4);
                    let institution: String = row.get(5);
                    let environment: String = row.get(6);
                    let parameters: String = row.get(7);
                    let details: String = row.get(8);
                    let attachment: String = row.get(9);
                    let hash: String = row.get(10);
                    let offset: i32 = row.get(11);
                    let timestamp: i32 = row.get(12);
                    entries.push(Entry {
                        id,
                        name,
                        experiment_time,
                        author,
                        email,
                        institution,
                        environment,
                        parameters,
                        details,
                        attachment,
                        hash,
                        offset,
                        timestamp,
                    });
                }
            }
            Err(e) => {
                error!("{}", e);
            }
        }
        // for row in  {
        //     let id: i32 = row.get(0);
        //     let name: String = row.get(1);
        //     let experiment_time: i32 = row.get(2);
        //     let author: String = row.get(3);
        //     let email: String = row.get(4);
        //     let institution: String = row.get(5);
        //     let environment: String = row.get(6);
        //     let parameters: String = row.get(7);
        //     let details: String = row.get(8);
        //     let attachment: String = row.get(9);
        //     let hash: String = row.get(10);
        //     let offset: i32 = row.get(11);
        //     let timestamp: i32 = row.get(12);
        //     entries.push(Entry {
        //         id,
        //         name,
        //         experiment_time,
        //         author,
        //         email,
        //         institution,
        //         environment,
        //         parameters,
        //         details,
        //         attachment,
        //         hash,
        //         offset,
        //         timestamp,
        //     });
        // }
        entries
    }

    pub fn get_entry(&mut self, id: i32) -> Result<Entry, String> {
        self.client.query_one("SELECT * FROM hyperdb WHERE id = ?", &[&id])
            .map(|row| {
                let id: i32 = row.get(0);
                let name: String = row.get(1);
                let experiment_time: i32 = row.get(2);
                let author: String = row.get(3);
                let email: String = row.get(4);
                let institution: String = row.get(5);
                let environment: String = row.get(6);
                let parameters: String = row.get(7);
                let details: String = row.get(8);
                let attachment: String = row.get(9);
                let hash: String = row.get(10);
                let offset: i32 = row.get(11);
                let timestamp: i32 = row.get(12);
                Entry {
                    id,
                    name,
                    experiment_time,
                    author,
                    email,
                    institution,
                    environment,
                    parameters,
                    details,
                    attachment,
                    hash,
                    offset,
                    timestamp,
                }
            })
            .map_err(|e| e.to_string())
    }

    pub fn insert(&mut self, id: i32, name: &str, experiment_time: i32, author: &str, email: &str, institution: &str, environment: &String, parameters: &String, details: &String, attachment: &String, hash: &str, offset: i32, timestamp: i32) -> Result<(), String> {
        let res = self.client.query("INSERT INTO hyperdb (id, name, experiment_time, author, email, institution, environment, parameters, details, attachment, hash, offset, timestamp, creator) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)", 
        &[&id, &name, &experiment_time, &author, &email, &institution, &environment, &parameters, &details, &attachment, &hash, &offset, &timestamp, &self.user]);
        match res {
            Ok(_) => {
                Ok(())
            }
            Err(e) => {
                error!("{}", e);
                Err(e.to_string())
            }
        }
    }

    pub fn insert_entry(&mut self, entry: &Entry) -> Result<(), String> {
        let res = self.client.execute(
            "INSERT INTO hyperdb (name, experiment_time, author, email, institution, environment, parameters, details, attachment, hash, offset, timestamp, creator) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)",
            &[
                &entry.name,
                &entry.experiment_time,
                &entry.author,
                &entry.email,
                &entry.institution,
                &entry.environment,
                &entry.parameters,
                &entry.details,
                &entry.attachment,
                &entry.hash,
                &entry.offset,
                &entry.timestamp,
                &self.user,
            ],
        );
        match res {
            Ok(_) => Ok(()),
            Err(e) => Err(e.to_string()),
        }
    }
}