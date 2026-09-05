# ABKGroup HypergraphPartitioning

This project attempts to benchmark hypergraph partitioning solutions in the context of VLSI, superseeding [TILOS-AI-Institute/HypergraphPartitioning](https://github.com/TILOS-AI-Institute/HypergraphPartitioning/tree/main).

The main site is located at https://vlsicad.ucsd.edu/partitioning. This repository contains the evaluator used to determine cutsizes (`golden_evaluator/`), as well as a handful of submitted solutions sets (`submitted_solutions/`). CI is also present on this repo to produce site database files from submitted solution sets (`src/`). The site's primary source code can be found [here on GitHub](https://github.com/ABKGroup/hgpleaderboard-site). The vast majority of solutions presented on the site are generated on ABKGroup servers and can be downloaded from the site. 

The benchmark hypergraphs used can be found [here on HuggingFace](https://huggingface.co/datasets/ABKGroup/hgp-benchmarks/tree/main).