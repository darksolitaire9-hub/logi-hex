use sqlx::SqlitePool;
use tokio::sync::{mpsc, oneshot};
use log::{info, error};

// The command payload sent over the MPSC queue
pub enum WriteCommand {
    ExecuteSql {
        sql: String,
        // Using String arguments for simplicity, but could be extended to typed arguments
        args: Vec<String>, 
        reply: oneshot::Sender<Result<u64, String>>,
    },
    Shutdown {
        reply: oneshot::Sender<()>,
    }
}

pub struct DbWriter {
    sender: mpsc::Sender<WriteCommand>,
}

impl DbWriter {
    pub fn new(pool: SqlitePool) -> Self {
        // Bounded queue of 100 to provide explicit backpressure.
        // If the UI attempts to fire 101 concurrent writes, it will await until space frees up.
        let (tx, mut rx) = mpsc::channel::<WriteCommand>(100);

        // Spawn the single-writer worker thread
        tokio::spawn(async move {
            info!("Starting Single-Writer MPSC SQLite Worker");
            
            while let Some(cmd) = rx.recv().await {
                match cmd {
                    WriteCommand::ExecuteSql { sql, args: _, reply } => {
                        // TODO: Implement actual SQL execution via sqlx using `args`
                        // For now, we simulate execution or construct queries
                        
                        // Example dynamic query execution (In a true app we'd bind arguments securely)
                        // This handles the single writer path aligned with SQLite
                        let result = sqlx::query(&sql)
                            .execute(&pool)
                            .await;

                        match result {
                            Ok(res) => {
                                let _ = reply.send(Ok(res.rows_affected()));
                            }
                            Err(e) => {
                                error!("MPSC SQLite Write Error: {}", e);
                                let _ = reply.send(Err(e.to_string()));
                            }
                        }
                    }
                    WriteCommand::Shutdown { reply } => {
                        info!("Draining MPSC Queue and Shutting Down Writer");
                        // Because we recv() inside a single thread, calling shutdown ensures
                        // that everything currently in the channel has been processed up to this message.
                        let _ = reply.send(());
                        break;
                    }
                }
            }
            info!("Single-Writer MPSC SQLite Worker Terminated");
        });

        DbWriter { sender: tx }
    }

    pub async fn execute(&self, sql: String, args: Vec<String>) -> Result<u64, String> {
        let (reply_tx, reply_rx) = oneshot::channel();
        
        let cmd = WriteCommand::ExecuteSql { sql, args, reply: reply_tx };
        
        // This will await (backpressure) if the bounded channel (100) is full
        if let Err(e) = self.sender.send(cmd).await {
            return Err(format!("Failed to enqueue write command: {}", e));
        }

        // Wait for the single-writer to execute and reply
        reply_rx.await.map_err(|e| format!("Worker crashed or dropped reply: {}", e))?
    }

    pub async fn shutdown(&self) {
        let (reply_tx, reply_rx) = oneshot::channel();
        if self.sender.send(WriteCommand::Shutdown { reply: reply_tx }).await.is_ok() {
            let _ = reply_rx.await;
        }
    }
}
