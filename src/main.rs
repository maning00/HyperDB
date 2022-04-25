use clap::Parser;
use tracing_subscriber::filter::LevelFilter;
use daemonlib::*;


/// HyperDB is a blockchain database, mainly for experimental data copyright protection applications. 
#[derive(Debug, Parser)]
struct Args {
    /// Bind the TCP server to this host.
    #[clap(short, long, default_value = "127.0.0.1")]
    host: String,

    /// Bind the TCP server to this port.
    #[clap(short, long, default_value = "26658")]
    port: u16,

    /// Increase output logging verbosity to DEBUG level.
    #[clap(short, long)]
    verbose: bool,

    /// Suppress all output logging (overrides --verbose).
    #[clap(short, long)]
    quiet: bool,
}

fn main() {
    let args = Args::parse();
    let log_level = if args.quiet {
        LevelFilter::OFF
    } else if args.verbose {
        LevelFilter::DEBUG
    } else {
        LevelFilter::INFO
    };
    tracing_subscriber::fmt().with_max_level(log_level).init();
    let mut hyperdb = HyperDBDriver::new(dbconnector::DBConnector::new("postgresql://postgres:maning00@10.25.127.19:5432/hyperdb"));
    let res = hyperdb.get_entries();
    println!("{:?}", res);
}
