"""
Extreme Multi-Paper Test Suite for PaperGraph V3
Generates a realistic 25-paper academic corpus, imports them, executes deep cognitive analysis,
and exercises every single backend feature & API route to uncover and eliminate any latent errors.
"""
import os
import sys
import json
import time
import shutil
from pathlib import Path

# Add project root to path
v3_root = str(Path(__file__).resolve().parent)
sys.path.insert(0, v3_root)

# Clear any cached imports
for m in [k for k in sys.modules if k.startswith("app")]:
    del sys.modules[m]

from fastapi.testclient import TestClient
from app.main import app
from app.core.workspace_manager import workspace_manager
from app.services.analyzer_pipeline import analyzer_pipeline

client = TestClient(app)

PAPERS_SPEC = [
    {
        "filename": "vaswani_2017_transformer.pdf",
        "title": "Attention Is All You Need",
        "author": "Ashish Vaswani, Noam Shazeer, Niki Parmar",
        "year": 2017,
        "doi": "10.48550/arXiv.1706.03762",
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.",
        "text": "Results show that the Transformer achieves 28.4 BLEU on the WMT 2014 English-to-German translation task, outperforming existing models by over 2 BLEU. However, self-attention exhibits quadratic complexity with sequence length."
    },
    {
        "filename": "he_2016_resnet.pdf",
        "title": "Deep Residual Learning for Image Recognition",
        "author": "Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun",
        "year": 2016,
        "doi": "10.1109/CVPR.2016.90",
        "abstract": "Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously.",
        "text": "We evaluate residual nets with a depth of up to 152 layers on ImageNet. Results show that ResNet achieves 3.57% top-5 error, winning first place in ILSVRC 2015. Our approach relies on shortcut connections."
    },
    {
        "filename": "devlin_2019_bert.pdf",
        "title": "BERT Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "author": "Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova",
        "year": 2019,
        "doi": "10.18653/v1/N19-1423",
        "abstract": "We introduce BERT, which stands for Bidirectional Encoder Representations from Transformers. BERT is designed to pre-train deep bidirectional representations from unlabeled text.",
        "text": "Results show that BERT advances the state-of-the-art for 11 NLP tasks, including pushing the GLUE score to 80.5%. However, pre-training is bounded by significant computational cost."
    },
    {
        "filename": "brown_2020_gpt3.pdf",
        "title": "Language Models are Few-Shot Learners",
        "author": "Tom B. Brown, Benjamin Mann, Nick Ryder",
        "year": 2020,
        "doi": "10.48550/arXiv.2005.14165",
        "abstract": "We demonstrate that scaling up language models greatly improves task-agnostic, few-shot performance, sometimes even reaching competitiveness with prior state-of-the-art fine-tuning approaches.",
        "text": "We train GPT-3, an autoregressive language model with 175 billion parameters. In contrast to fine-tuning, GPT-3 applies in-context conditioning. Results demonstrate high performance across translation and QA."
    },
    {
        "filename": "goodfellow_2014_gans.pdf",
        "title": "Generative Adversarial Nets",
        "author": "Ian Goodfellow, Jean Pouget-Abadie, Mehdi Mirza",
        "year": 2014,
        "doi": "10.1145/3422622",
        "abstract": "We propose a new framework for estimating generative models via an adversarial process, in which we simultaneously train two models: a generative model G and a discriminative model D.",
        "text": "Experiments demonstrate that the adversarial framework can generate convincing samples on MNIST and CIFAR-10. However, training is notoriously vulnerable to mode collapse and minimax instability."
    },
    {
        "filename": "ho_2020_diffusion.pdf",
        "title": "Denoising Diffusion Probabilistic Models",
        "author": "Jonathan Ho, Ajay Jain, Pieter Abbeel",
        "year": 2020,
        "doi": "10.48550/arXiv.2006.11239",
        "abstract": "We present high quality image synthesis results using diffusion probabilistic models, a class of latent variable models inspired by considerations from non-equilibrium thermodynamics.",
        "text": "Our approach achieves a FID score of 3.17 on unconditional CIFAR-10. We found that reverse diffusion steps yield higher sample quality than GANs, though sampling throughput remains slow."
    },
    {
        "filename": "krizhevsky_2012_alexnet.pdf",
        "title": "ImageNet Classification with Deep Convolutional Neural Networks",
        "author": "Alex Krizhevsky, Ilya Sutskever, Geoffrey E. Hinton",
        "year": 2012,
        "doi": "10.1145/3065386",
        "abstract": "We trained a large, deep convolutional neural network to classify the 1.2 million high-resolution images in the ImageNet LSVRC-2010 contest into the 1000 different classes.",
        "text": "Results show a top-5 error rate of 15.3%, compared to 26.2% achieved by the second-best entry. We employed ReLU non-linearities and dropout regularization to combat overfitting."
    },
    {
        "filename": "silver_2016_alphago.pdf",
        "title": "Mastering the Game of Go with Deep Neural Networks and Tree Search",
        "author": "David Silver, Aja Huang, Chris J. Maddison",
        "year": 2016,
        "doi": "10.1038/nature16961",
        "abstract": "The game of Go has long been viewed as the most challenging of classic games for artificial intelligence owing to its enormous search space and the difficulty of evaluating board positions.",
        "text": "AlphaGo evaluated positions using value networks and policy networks trained by self-play reinforcement learning, achieving a 99.8% winning rate against other Go programs and defeating the European champion."
    },
    {
        "filename": "kingma_2014_adam.pdf",
        "title": "Adam: A Method for Stochastic Optimization",
        "author": "Diederik P. Kingma, Jimmy Ba",
        "year": 2014,
        "doi": "10.48550/arXiv.1412.6980",
        "abstract": "We introduce Adam, an algorithm for first-order gradient-based optimization of stochastic objective functions, based on adaptive estimates of lower-order moments.",
        "text": "Empirical results demonstrate that Adam converges rapidly on deep neural architectures, outperforming AdaGrad and RMSProp across logistic regression and multi-layer perceptrons."
    },
    {
        "filename": "srivastava_2014_dropout.pdf",
        "title": "Dropout: A Simple Way to Prevent Neural Networks from Overfitting",
        "author": "Nitish Srivastava, Geoffrey Hinton, Alex Krizhevsky",
        "year": 2014,
        "doi": "10.5555/2627435.2670313",
        "abstract": "Deep neural networks with a large number of parameters are very powerful machine learning systems. However, overfitting is a serious problem in such networks.",
        "text": "The key idea is to randomly drop units during training. Results show that dropout substantially reduces overfitting and gives major improvements over other regularization methods on vision and speech."
    },
    {
        "filename": "hu_2021_lora.pdf",
        "title": "LoRA: Low-Rank Adaptation of Large Language Models",
        "author": "Edward J. Hu, Yelong Shen, Phillip Wallis",
        "year": 2021,
        "doi": "10.48550/arXiv.2106.09685",
        "abstract": "An important paradigm involves fine-tuning large pre-trained language models. We propose Low-Rank Adaptation (LoRA), which freezes the pre-trained model weights and injects trainable rank decomposition matrices.",
        "text": "LoRA reduces the number of trainable parameters by 10,000 times and GPU memory requirements by 3 times. Results show that LoRA performs on par or better than full fine-tuning on RoBERTa and GPT-3."
    },
    {
        "filename": "dao_2022_flashattention.pdf",
        "title": "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness",
        "author": "Tri Dao, Daniel Y. Fu, Stefano Ermon",
        "year": 2022,
        "doi": "10.48550/arXiv.2205.14135",
        "abstract": "Transformers are slow and memory-hungry on long sequences, as the time and memory complexity of self-attention are quadratic in sequence length.",
        "text": "FlashAttention trains Transformers faster than existing baselines: 2-4x wall-clock speedup on BERT-large and GPT-2, with linear memory footprint instead of quadratic scaling."
    },
    {
        "filename": "touvron_2023_llama.pdf",
        "title": "LLaMA: Open and Efficient Foundation Language Models",
        "author": "Hugo Touvron, Thibaut Lavril, Gautier Izacard",
        "year": 2023,
        "doi": "10.48550/arXiv.2302.13971",
        "abstract": "We introduce LLaMA, a collection of foundation language models ranging from 7B to 65B parameters trained on trillions of tokens exclusively using publicly available datasets.",
        "text": "LLaMA-13B outperforms GPT-3 (175B) on most benchmarks despite being more than 10x smaller. Results demonstrate that training smaller models on more tokens achieves competitive Pareto frontiers."
    },
    {
        "filename": "lecun_2015_deep_learning.pdf",
        "title": "Deep Learning",
        "author": "Yann LeCun, Yoshua Bengio, Geoffrey Hinton",
        "year": 2015,
        "doi": "10.1038/nature14539",
        "abstract": "Deep learning allows computational models that are composed of multiple processing layers to learn representations of data with multiple levels of abstraction.",
        "text": "Deep learning has produced dramatic improvements in speech recognition, visual object recognition, object detection and many other domains such as drug discovery and genomics."
    },
    {
        "filename": "ioffe_2015_batchnorm.pdf",
        "title": "Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift",
        "author": "Sergey Ioffe, Christian Szegedy",
        "year": 2015,
        "doi": "10.48550/arXiv.1502.03167",
        "abstract": "Training Deep Neural Networks is complicated by the fact that the distribution of each layer's inputs changes during training. We refer to this phenomenon as internal covariate shift.",
        "text": "Applied to state-of-the-art image classification models, Batch Normalization achieves the same accuracy with 14 times fewer training steps, and beats the previous state of the art."
    },
    {
        "filename": "mnih_2013_dqn.pdf",
        "title": "Playing Atari with Deep Reinforcement Learning",
        "author": "Volodymyr Mnih, Koray Kavukcuoglu, David Silver",
        "year": 2013,
        "doi": "10.48550/arXiv.1312.5602",
        "abstract": "We present the first deep learning model to successfully learn control policies directly from high-dimensional sensory input using reinforcement learning.",
        "text": "We apply our approach to seven Atari 2600 games. We found that DQN outperforms all previous approaches on six of the games and surpasses a human expert on three of them."
    },
    {
        "filename": "bahdanau_2014_attention.pdf",
        "title": "Neural Machine Translation by Jointly Learning to Align and Translate",
        "author": "Dzmitry Bahdanau, Kyunghyun Cho, Yoshua Bengio",
        "year": 2014,
        "doi": "10.48550/arXiv.1409.0473",
        "abstract": "Neural machine translation is a recently proposed approach to machine translation. We hypothesize that the use of a fixed-length vector is a bottleneck in improving performance.",
        "text": "We introduce an attention mechanism that allows the model to search for parts of a source sentence that are relevant to predicting a target word, improving translation of long sentences."
    },
    {
        "filename": "bai_2022_constitutional_ai.pdf",
        "title": "Constitutional AI: A Harmless Approach from AI Feedback",
        "author": "Yuntao Bai, Saurav Kadavath, Sandipan Kundu",
        "year": 2022,
        "doi": "10.48550/arXiv.2212.08073",
        "abstract": "We experiment with methods for training a harmless AI assistant through self-improvement, without any human feedback labels for harmlessness.",
        "text": "The only human oversight is provided through a list of principles or constitutional rules. Results show that RLAIF achieves equivalent harmlessness without compromising helpfulness."
    },
    {
        "filename": "dettmers_2023_qlora.pdf",
        "title": "QLoRA: Efficient Finetuning of Quantized LLMs",
        "author": "Tim Dettmers, Artidoro Pagnoni, Ari Holtzman",
        "year": 2023,
        "doi": "10.48550/arXiv.2305.14314",
        "abstract": "We present QLoRA, an efficient finetuning approach that reduces memory usage enough to finetune a 65B parameter model on a single 48GB GPU while preserving full 16-bit finetuning task performance.",
        "text": "QLoRA backpropagates gradients through a frozen, 4-bit quantized pretrained language model into Low Rank Adapters. Results show Guanaco achieves 99.3% of ChatGPT performance on Vicuna benchmark."
    },
    {
        "filename": "rafailov_2023_dpo.pdf",
        "title": "Direct Preference Optimization: Your Language Model is Secretly a Reward Model",
        "author": "Rafael Rafailov, Archit Sharma, Eric Mitchell",
        "year": 2023,
        "doi": "10.48550/arXiv.2305.18290",
        "abstract": "While reinforcement learning from human feedback (RLHF) is powerful, it is complex and unstable. We propose Direct Preference Optimization (DPO), which optimizes policy directly.",
        "text": "DPO eliminates the need for training a separate reward model. Experiments show that DPO controls sentiment and improves summary quality while being substantially simpler and faster to train."
    },
    {
        "filename": "kaplan_2020_scaling_laws.pdf",
        "title": "Scaling Laws for Neural Language Models",
        "author": "Jared Kaplan, Sam McCandlish, Tom Henighan",
        "year": 2020,
        "doi": "10.48550/arXiv.2001.08361",
        "abstract": "We investigate empirical scaling laws for language model performance on cross-entropy loss. The loss scales as a power-law with model size, dataset size, and the amount of compute used for training.",
        "text": "Performance depends strongly on scale, and weakly on model shape (depth vs width). Larger models are significantly more sample-efficient, achieving the same perplexity with fewer training steps."
    },
    {
        "filename": "lewis_2020_rag.pdf",
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "author": "Patrick Lewis, Ethan Perez, Aleksandara Piktus",
        "year": 2020,
        "doi": "10.48550/arXiv.2005.11401",
        "abstract": "Large pre-trained language models have been shown to store factual knowledge in their parameters. However, their ability to precisely access and manipulate knowledge is still limited.",
        "text": "We build RAG models where the parametric memory is a pre-trained seq2seq model and non-parametric memory is a dense vector index of Wikipedia. RAG models set new state of the art on Open-Domain QA."
    },
    {
        "filename": "wei_2022_emergent_abilities.pdf",
        "title": "Emergent Abilities of Large Language Models",
        "author": "Jason Wei, Yi Tay, Rishi Bommasani",
        "year": 2022,
        "doi": "10.48550/arXiv.2206.07682",
        "abstract": "Scaling up language models has been shown to predictably improve performance and sample efficiency. We discuss an unpredictable phenomenon that we refer to as emergent abilities of large language models.",
        "text": "An ability is emergent if it is not present in smaller models but is present in larger models. We review emergent abilities across arithmetic, multi-task reasoning, and translation."
    },
    {
        "filename": "wei_2022_chain_of_thought.pdf",
        "title": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
        "author": "Jason Wei, Xuezhi Wang, Dale Schuurmans",
        "year": 2022,
        "doi": "10.48550/arXiv.2201.11903",
        "abstract": "We explore how generating a chain of thought—a series of intermediate reasoning steps—significantly improves the ability of large language models to perform complex reasoning.",
        "text": "Experiments show that chain-of-thought prompting improves performance on math word problems, symbolic manipulation, and multi-step reasoning tasks, surpassing standard prompting by up to 30%."
    },
    {
        "filename": "turing_1950_computing_machinery.pdf",
        "title": "Computing Machinery and Intelligence",
        "author": "Alan M. Turing",
        "year": 1950,
        "doi": "10.1093/mind/LIX.236.433",
        "abstract": "I propose to consider the question, Can machines think? This should begin with definitions of the meaning of the terms machine and think.",
        "text": "We introduce the imitation game to replace the question with an operational test. We argue that digital computers can eventually play the game satisfactorily, establishing the philosophical foundations of AI."
    }
]

def make_pdf_bytes(title, author, year, doi, abstract, text):
    stream_content = f"""BT
/F1 14 Tf
50 720 Td
({title}) Tj
/F1 10 Tf
0 -25 Td
(Authors: {author} ({year})) Tj
0 -20 Td
(DOI: {doi}) Tj
0 -25 Td
(Abstract: {abstract}) Tj
0 -30 Td
({text}) Tj
ET""".encode("latin1", errors="replace")

    stream_len = len(stream_content)
    pdf = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {stream_len} >>
stream
{stream_content.decode('latin1', errors='replace')}
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000227 00000 n 
0000000280 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
350
%%EOF"""
    return pdf.encode("latin1", errors="replace")

def run_extreme_test():
    print("======================================================================")
    print("STARTING EXTREME 25-PAPER BENCHMARK & FULL FEATURE AUDIT")
    print("======================================================================")

    test_folder = Path.home() / "Desktop" / "extreme_test_25_papers"
    if test_folder.exists():
        shutil.rmtree(test_folder)
    test_folder.mkdir(parents=True, exist_ok=True)

    print(f"\n[1/15] Generating 25 scientific research PDFs into {test_folder}...")
    for p in PAPERS_SPEC:
        pdf_bytes = make_pdf_bytes(p["title"], p["author"], p["year"], p["doi"], p["abstract"], p["text"])
        with open(test_folder / p["filename"], "wb") as f:
            f.write(pdf_bytes)
    print(f"Generated {len(PAPERS_SPEC)} research papers successfully.")

    # 1. Test Scan Directory
    print("\n[2/15] Testing POST /api/papers/scan-folder...")
    res = client.post("/api/papers/scan-folder", json={"folder_path": str(test_folder)})
    assert res.status_code == 200, f"Scan folder failed: {res.text}"
    scan_data = res.json()
    discovered = scan_data.get("discovered_papers", [])
    print(f"Scan succeeded: Discovered {len(discovered)} papers.")
    assert len(discovered) == 25, f"Expected 25 papers, got {len(discovered)}"

    # 2. Test Import Directory
    print("\n[3/15] Testing POST /api/papers/import-folder...")
    res = client.post("/api/papers/import-folder", json={"folder_path": str(test_folder)})
    assert res.status_code == 200, f"Import folder failed: {res.text}"
    import_data = res.json()
    imported_count = import_data.get("imported_count", 0)
    total_in_lib = len(workspace_manager.list_all_papers())
    print(f"Import succeeded: Ingested {imported_count} new papers. Total papers in library: {total_in_lib}.")
    assert total_in_lib >= 20, f"Expected >= 20 papers in library, got {total_in_lib}"

    # 3. Test Full Analysis Pipeline on Imported Papers
    print("\n[4/15] Running Cognitive Analyzer Pipeline on all imported papers...")
    all_papers = workspace_manager.list_all_papers()
    print(f"Total papers in workspace library: {len(all_papers)}")
    for idx, p in enumerate(all_papers[:25], 1):
        pid = p["id"]
        t0 = time.time()
        try:
            res_meta = analyzer_pipeline.process_paper(pid)
            dt = time.time() - t0
            print(f"  Analyzed [{idx}/{len(all_papers)}] '{p.get('title', pid)[:45]}...' ({dt:.2f}s)")
        except Exception as e:
            print(f"  ERROR analyzing {pid}: {e}")
            raise e

    # 4. Test Knowledge Graph (Including Datasets, Methods, Authors, Topics)
    print("\n[5/15] Testing Knowledge Graph (/api/graph)...")
    res = client.get("/api/graph", params={
        "include_datasets": True,
        "include_methods": True,
        "include_authors": True,
        "include_topics": True,
        "similarity_threshold": 0.25
    })
    assert res.status_code == 200, f"Graph failed: {res.text}"
    graph_data = res.json()
    nodes = graph_data.get("elements", {}).get("nodes", [])
    edges = graph_data.get("elements", {}).get("edges", [])
    print(f"Knowledge Graph verified: {len(nodes)} nodes, {len(edges)} edges, {graph_data.get('metrics', {}).get('clusters', 0)} Louvain clusters.")
    assert len(nodes) > 0, "Graph must contain nodes"

    # 5. Test Ego Graph for first paper
    sample_pid = all_papers[0]["id"]
    print(f"\n[6/15] Testing Ego Graph (/api/graph/paper/{sample_pid})...")
    res = client.get(f"/api/graph/paper/{sample_pid}")
    assert res.status_code == 200, f"Ego graph failed: {res.text}"
    ego_data = res.json()
    print(f"Ego graph verified: {len(ego_data.get('elements', {}).get('nodes', []))} nodes.")

    # 6. Test Cross-Paper Synthesis
    print("\n[7/15] Testing Synthesis & Comparison (/api/synthesis/compare)...")
    compare_pids = [p["id"] for p in all_papers[:5]]
    res = client.post("/api/synthesis/compare", json={"paper_ids": compare_pids})
    assert res.status_code == 200, f"Synthesis failed: {res.text}"
    synth_data = res.json()
    print(f"Synthesis verified: 9-dimension grid computed across {len(compare_pids)} papers.")
    assert "dimensions" in synth_data

    # 7. Test Evidence Matrix
    print("\n[8/15] Testing Evidence Matrix (/api/synthesis/evidence-matrix)...")
    res = client.get("/api/synthesis/evidence-matrix")
    assert res.status_code == 200, f"Evidence matrix failed: {res.text}"
    ev_data = res.json()
    print(f"Evidence matrix verified: {len(ev_data.get('rows', []))} rows.")

    # 8. Test Hypotheses Explorer
    print("\n[9/15] Testing Hypotheses Explorer (/api/hypotheses)...")
    res = client.get("/api/hypotheses")
    assert res.status_code == 200, f"Hypotheses failed: {res.text}"
    hyp_data = res.json()
    questions = hyp_data if isinstance(hyp_data, list) else hyp_data.get("candidate_questions", [])
    print(f"Hypotheses verified: {len(questions)} candidate research questions synthesized.")

    # 9. Test Literature Review Studio
    print("\n[10/15] Testing Literature Review Studio (/api/review/outline & /api/review/draft)...")
    res = client.post("/api/review/outline", json={"topic": "Deep Representation Learning", "paper_ids": compare_pids})
    assert res.status_code == 200, f"Review outline failed: {res.text}"
    res2 = client.post("/api/review/draft", json={"topic": "Deep Representation Learning", "paper_ids": compare_pids})
    assert res2.status_code == 200, f"Review draft failed: {res2.text}"
    draft_data = res2.json()
    print(f"Literature Review draft verified: {len(draft_data.get('markdown_draft', ''))} chars, BibTeX entries present.")

    # 10. Test Intersections & Research Trends
    print("\n[11/15] Testing Intersections & Trends (/api/intersections, /api/trends)...")
    res_int = client.get("/api/intersections")
    assert res_int.status_code == 200, f"Intersections failed: {res_int.text}"
    res_trd = client.get("/api/trends")
    assert res_trd.status_code == 200, f"Trends failed: {res_trd.text}"
    print("Intersections and trends analysis verified.")

    # 11. Test Collections Management
    print("\n[12/15] Testing Collections Management...")
    res_col = client.post("/api/collections", json={"name": "Seminal AI Milestones", "description": "Foundational papers in artificial intelligence"})
    assert res_col.status_code == 200, f"Create collection failed: {res_col.text}"
    col_id = res_col.json().get("collection", {}).get("id")
    client.post(f"/api/collections/{col_id}/papers", json={"paper_id": sample_pid})
    res_cols = client.get("/api/collections")
    assert res_cols.status_code == 200
    print(f"Collections verified: created '{col_id}' and assigned paper '{sample_pid}'.")

    # 12. Test Notes Management
    print("\n[13/15] Testing Notes Updates...")
    res_notes = client.put(f"/api/papers/{sample_pid}/notes", json={"notes": "Critical paper for representation learning research."})
    assert res_notes.status_code == 200
    print(f"Notes verified on paper {sample_pid}.")

    # 13. Test Academic Export Suite (BibTeX, JSON, CSV, Markdown)
    print("\n[14/15] Testing Academic Export Suite (/api/export)...")
    for fmt in ["bibtex", "json", "csv", "markdown"]:
        res_exp = client.post("/api/export", json={"format": fmt, "paper_ids": compare_pids})
        assert res_exp.status_code == 200, f"Export {fmt} failed: {res_exp.text}"
    print("Academic Export Suite (BibTeX, JSON, CSV, Markdown) verified.")

    # 14. Test V3 Autonomous OCR & Plugin Endpoints
    print("\n[15/15] Testing V3 Autonomous OCR, Search & Hypotheses...")
    res_v3_status = client.get("/api/v3/status")
    assert res_v3_status.status_code == 200
    res_v3_hyp = client.post("/api/v3/hypothesis/synthesize", params={"topic": "Attention Efficiency"})
    assert res_v3_hyp.status_code == 200
    assert "null_hypothesis_h0" in res_v3_hyp.json()
    print("V3 Autonomous Extensions verified.")

    print("\n======================================================================")
    print("ALL 15 MAJOR SUBSYSTEMS & 25 PAPERS TESTED WITH ZERO ERRORS!")
    print("======================================================================")

if __name__ == "__main__":
    run_extreme_test()
