import os
import shutil
from pathlib import Path

def migrate_medpart_solutions(source_dir: str, dest_dir: str):
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)
    
    if not source_path.exists():
        print(f"Source directory {source_path} does not exist.")
        return

    for root, dirs, files in os.walk(source_path):
        for file in files:
            if file == "README.md":
                continue
            
            # Example file: sparcT1_core.hgr.medpart.ubfactor.2.part.2.score.625
            file_path = Path(root) / file
            
            # Determine K and IMB based on directory structure
            # Example root: ../TILOS-HGP/medpart_solutions/2_way/ub_factor_2
            parts = Path(root).parts
            k_str = parts[-2] # "2_way"
            imb_str = parts[-1] # "ub_factor_2"
            
            if not k_str.endswith("_way") or not imb_str.startswith("ub_factor_"):
                print(f"Skipping directory with unexpected structure: {root}")
                continue
            
            k = int(k_str.split("_")[0])
            imb = int(imb_str.split("_")[-1])
            
            # Parse benchmark name
            benchmark_name = file.split('.hgr.medpart')[0]
            
            # Dataset mapping, assume titan23 since they match the Titan23 benchmarks
            dataset = "titan23"
            
            # Target path: submitted_solutions/<benchmark_dataset>/<partitioner>/k_<x>/imb_<y>/<benchmark_name>.part
            target_dir = dest_path / dataset / "medpart" / f"k_{k}" / f"imb_{imb}"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            target_file = target_dir / f"{benchmark_name}.part"
            
            shutil.copy(file_path, target_file)
            print(f"Copied {file} -> {target_file}")

if __name__ == "__main__":
    source = "../TILOS-HGP/medpart_solutions"
    dest = "submitted_solutions"
    print(f"Migrating from {source} to {dest}...")
    migrate_medpart_solutions(source, dest)
    print("Migration complete.")
