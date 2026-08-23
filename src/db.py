import sqlite3
import uuid
from dataclasses import dataclass, asdict, field
from typing import Optional, List
from pathlib import Path

"""
Hypergraph Partitioning Leaderboard - Database Creation Library
---------------------------------------------------------------
This library provides a Pythonic, object-oriented way to create and populate 
SQLite databases that perfectly conform to the `hgp_amur_schema`.

You can use this library to package your partitioner's results into a clean 
SQLite database, which can then be submitted and merged into the main leaderboard.

Artifact Paths:
For `partition_path`, `stdout_path`, and `stderr_path`, you can provide either:
1. Absolute local file paths (e.g., `/home/user/results/my_graph.part`)
2. Public URLs (e.g., `https://my-bucket.s3.amazonaws.com/results/my_graph.part`)
"""

@dataclass
class Executable:
    """Represents a partitioner or tool in the executables table."""
    executable_id: str
    display_name: str
    path: Optional[str] = None
    sha256: Optional[str] = None
    command_template: Optional[str] = None

@dataclass
class BenchmarkItem:
    """Represents a hypergraph or test graph in the benchmark_items table."""
    item_id: str
    family: Optional[str] = None
    source_kind: str = "legacy_public"
    num_hyperedges: Optional[int] = None
    num_vertices: Optional[int] = None
    path: Optional[str] = None
    feature_json: Optional[str] = None

@dataclass
class EvalResult:
    """Represents a single partitioning run in the eval_results table."""
    run_id: str
    executable_id: str
    item_id: str
    k: int
    seed: int
    status: str = "ok"
    
    # Optional but highly recommended metrics
    validated_cut: Optional[int] = None
    time_cap_s: Optional[int] = None
    ubfactor: Optional[float] = None
    balance_json: Optional[str] = None
    runner_wall_time_s: Optional[float] = None
    
    # Artifact paths (Local absolute paths or HTTP/HTTPS URLs)
    partition_path: Optional[str] = None
    stdout_path: Optional[str] = None
    stderr_path: Optional[str] = None
    
    # Extra technical metrics
    threads: Optional[int] = None
    legal: Optional[int] = None
    max_rss_kb: Optional[int] = None
    error_class: Optional[str] = None
    gap_to_legacy_best: Optional[float] = None
    fallback_any: Optional[int] = None
    fallback_primary: Optional[str] = None
    fallback_json: Optional[str] = None
    native_clean: Optional[int] = None
    runner_over_cap: Optional[int] = None
    over_cap_s: Optional[float] = None
    raw_json: Optional[str] = None
    
    # Auto-generated if not provided
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))

class LeaderboardDB:
    """Manager class for creating and populating the leaderboard SQLite database."""
    
    def __init__(self, db_path: str | Path):
        """Initializes the connection to the SQLite database."""
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        
    def init_schema(self):
        """Creates the necessary tables if they do not exist."""
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS executables (
              executable_id text primary key,
              display_name text not null,
              path text,
              sha256 text,
              command_template text
            );

            CREATE TABLE IF NOT EXISTS benchmark_items (
              item_id text primary key,
              family text,
              num_hyperedges integer,
              source_kind text,
              path text,
              num_vertices integer,
              feature_json text
            );

            CREATE TABLE IF NOT EXISTS eval_results (
              result_id text primary key,
              run_id text not null,
              executable_id text not null,
              item_id text not null,
              k integer,
              ubfactor real,
              time_cap_s integer,
              threads integer,
              seed integer,
              status text,
              legal integer,
              validated_cut integer,
              balance_json text,
              runner_wall_time_s real,
              max_rss_kb integer,
              error_class text,
              gap_to_legacy_best real,
              fallback_any integer,
              fallback_primary text,
              fallback_json text,
              native_clean integer,
              runner_over_cap integer,
              over_cap_s real,
              partition_path text,
              stdout_path text,
              stderr_path text,
              raw_json text
            );
        ''')
        self.conn.commit()

    def add_executable(self, exe: Executable):
        """Inserts an Executable into the database."""
        query = '''
            INSERT OR REPLACE INTO executables 
            (executable_id, display_name, path, sha256, command_template)
            VALUES (:executable_id, :display_name, :path, :sha256, :command_template)
        '''
        self.conn.execute(query, asdict(exe))
        self.conn.commit()

    def add_benchmark_item(self, item: BenchmarkItem):
        """Inserts a BenchmarkItem into the database."""
        query = '''
            INSERT OR REPLACE INTO benchmark_items 
            (item_id, family, source_kind, num_hyperedges, num_vertices, path, feature_json)
            VALUES (:item_id, :family, :source_kind, :num_hyperedges, :num_vertices, :path, :feature_json)
        '''
        self.conn.execute(query, asdict(item))
        self.conn.commit()

    def add_eval_result(self, result: EvalResult):
        """Inserts an EvalResult into the database."""
        query = '''
            INSERT OR REPLACE INTO eval_results (
              result_id, run_id, executable_id, item_id, k, ubfactor, time_cap_s, threads, seed,
              status, legal, validated_cut, balance_json, runner_wall_time_s, max_rss_kb, error_class,
              gap_to_legacy_best, fallback_any, fallback_primary, fallback_json, native_clean,
              runner_over_cap, over_cap_s, partition_path, stdout_path, stderr_path, raw_json
            ) VALUES (
              :result_id, :run_id, :executable_id, :item_id, :k, :ubfactor, :time_cap_s, :threads, :seed,
              :status, :legal, :validated_cut, :balance_json, :runner_wall_time_s, :max_rss_kb, :error_class,
              :gap_to_legacy_best, :fallback_any, :fallback_primary, :fallback_json, :native_clean,
              :runner_over_cap, :over_cap_s, :partition_path, :stdout_path, :stderr_path, :raw_json
            )
        '''
        self.conn.execute(query, asdict(result))
        self.conn.commit()

    def close(self):
        """Closes the database connection."""
        self.conn.close()

if __name__ == "__main__":
    import json
    
    print("Running db.py example...")
    # Example Usage
    db = LeaderboardDB("my_submission.db")
    db.init_schema()
    
    # Add your tool
    my_tool = Executable(
        executable_id="my_awesome_tool_v1",
        display_name="My Awesome Tool (v1)"
    )
    db.add_executable(my_tool)
    
    # Add a graph if it doesn't already exist in the master database (optional)
    graph = BenchmarkItem(
        item_id="dpl.ucsd.edu__Bump_2911.mtx",
        family="dac2012",
        num_hyperedges=10000
    )
    db.add_benchmark_item(graph)
    
    # Add a result! Notice we use a URL for the partition path.
    result = EvalResult(
        run_id="run_001",
        executable_id="my_awesome_tool_v1",
        item_id="dpl.ucsd.edu__Bump_2911.mtx",
        k=2,
        seed=42,
        ubfactor=1.0,
        time_cap_s=60,
        validated_cut=450,
        balance_json=json.dumps({"max_deviation_pct": 0.5}),
        runner_wall_time_s=15.4,
        partition_path="https://my-bucket.s3.amazonaws.com/results/run_001.part"
    )
    db.add_eval_result(result)
    
    db.close()
    print("Successfully created 'my_submission.db'!")
