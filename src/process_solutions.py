import os
import zstandard as zstd
import tempfile
import subprocess
from pathlib import Path
from huggingface_hub import hf_hub_download
from db import LeaderboardDB, Executable, BenchmarkItem, EvalResult

# Add golden_evaluator to path if needed or import directly
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from golden_evaluator.utils import Evaluator

def decompress_zst(zst_path, output_path):
    with open(zst_path, 'rb') as compressed:
        dctx = zstd.ZstdDecompressor()
        with open(output_path, 'wb') as uncompressed:
            dctx.copy_stream(compressed, uncompressed)

def get_git_info(file_path):
    try:
        # Get the commit hash for the file. Use dirty if uncommitted.
        status = subprocess.check_output(["git", "status", "--porcelain", str(file_path)]).decode('utf-8').strip()
        if status:
            commit_hash = "dirty"
        else:
            commit_hash = subprocess.check_output(["git", "log", "-1", "--format=%H", "--", str(file_path)]).decode('utf-8').strip()
            if not commit_hash:
                commit_hash = "dirty"
    except Exception:
        commit_hash = "dirty"
        
    return commit_hash

def process_solutions(solutions_dir: str, db_path: str):
    db = LeaderboardDB(db_path)
    db.init_schema()

    solutions_path = Path(solutions_dir)
    if not solutions_path.exists():
        print(f"Solutions directory {solutions_path} does not exist.")
        return

    # Track seen executables and benchmarks to avoid redundant DB insertions
    seen_executables = set()
    seen_benchmarks = set()

    for root, dirs, files in os.walk(solutions_path):
        for file in files:
            if not file.endswith(".part"):
                continue

            file_path = Path(root) / file
            
            # Extract metadata from path: submitted_solutions/<dataset>/<partitioner>/k_<x>/imb_<y>/<benchmark>.part
            parts = file_path.relative_to(solutions_path).parts
            if len(parts) != 5:
                print(f"Skipping {file_path} due to unexpected structure.")
                continue

            dataset = parts[0]
            partitioner = parts[1]
            k_str = parts[2]
            imb_str = parts[3]
            benchmark_name = parts[4].removesuffix('.part')
            
            k = int(k_str.split("_")[1])
            imb = int(imb_str.split("_")[1])
            
            executable_id = partitioner
            if executable_id not in seen_executables:
                db.add_executable(Executable(
                    executable_id=executable_id,
                    display_name=executable_id.capitalize()
                ))
                seen_executables.add(executable_id)
            
            item_id = f"{dataset}::{benchmark_name}.hgr"
            if item_id not in seen_benchmarks:
                db.add_benchmark_item(BenchmarkItem(
                    item_id=item_id,
                    family=dataset,
                    source_kind="imported"
                ))
                seen_benchmarks.add(item_id)
                
            # Download and evaluate
            try:
                print(f"Fetching {dataset}/{benchmark_name}.hgr.zst from Hugging Face...")
                hf_path = hf_hub_download(repo_id="ABKGroup/hgp-benchmarks", filename=f"{dataset}/{benchmark_name}.hgr.zst", repo_type="dataset")
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    hgr_path = Path(temp_dir) / f"{benchmark_name}.hgr"
                    decompress_zst(hf_path, hgr_path)
                    
                    print(f"Evaluating {file_path} (k={k}, imb={imb})")
                    cut, blocks_balance, num_vertices, num_hyperedges = Evaluator(
                        str(hgr_path), str(file_path), k, imb
                    )
                    
                    if cut == 1e9:
                        print(f"Evaluation failed for {file_path}")
                        status = "error"
                        legal = 0
                        cut = None
                    else:
                        print(f"Cut: {cut}")
                        status = "ok"
                        legal = 1
                    
                    # Update benchmark with counts if not already set (since we have them from evaluation)
                    db.add_benchmark_item(BenchmarkItem(
                        item_id=item_id,
                        family=dataset,
                        source_kind="imported",
                        num_vertices=num_vertices,
                        num_hyperedges=num_hyperedges
                    ))

                    commit_hash = get_git_info(file_path)
                    path_underscores = str(file_path.relative_to(solutions_path)).replace('/', '_')
                    run_id = f"imported__git{commit_hash}__{path_underscores}"
                    
                    # Construct GitHub raw URL for partition_path
                    if commit_hash != "dirty":
                        # Assume github repository is current remote origin, but we don't have user/repo context here easily
                        # So we will just store a relative path or construct a generic one. Let's use relative for now, or just the file path
                        # Actually, instruction says: link to this solution in the raw githubusercontent
                        try:
                            remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"]).decode('utf-8').strip()
                            # Convert git@github.com:user/repo.git or https://github.com/user/repo.git to raw URL
                            # Simplified parsing:
                            if "github.com" in remote_url:
                                parts = remote_url.split("github.com")[-1].strip(":/").replace(".git", "").split("/")
                                user, repo = parts[0], parts[1]
                                raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/{commit_hash}/{file_path}"
                            else:
                                raw_url = str(file_path)
                        except Exception:
                            raw_url = str(file_path)
                    else:
                        raw_url = str(file_path)

                    db.add_eval_result(EvalResult(
                        run_id=run_id,
                        executable_id=executable_id,
                        item_id=item_id,
                        k=k,
                        seed=0,
                        status=status,
                        validated_cut=cut,
                        legal=legal,
                        partition_path=raw_url,
                        ubfactor=imb
                    ))
            
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    db.close()
    print("Database processing complete.")

if __name__ == "__main__":
    process_solutions("submitted_solutions", "leaderboard.db")
