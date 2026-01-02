> Part of **AGIPragma** research program.  
This repository contains foundational ideas and intuitions about AGI.
## AGIPragma links
- **AGI-Development (framework + doctrine + catalogue):** https://github.com/zabinskirafal/AGI-Development
- **developmental-agi-sandbox (benchmark):** https://github.com/zabinskirafal/developmental-agi-sandbox
## Authorship & commercialization
- **Author:** Rafał Żabiński  
- Research and commercial R&D use are permitted.
- **Commercialization (revenue, paid products/services, SaaS, licensing)** requires a separate commercial license from the author.

**WAŻNE – Licencja i zasady użycia**

**Darmowe w 100 % ** dla:
- badań naukowych
- edukacji
- projektów niekomercyjnych
- hobbystów i open-source

**Komercyjne wykorzystanie** (płatne modele, SaaS, usługi, trening zamkniętych AGI, produkty zar, enterprise)  
→ **wymaga mojej zgody i uczciwego podzielenia się zyskiem**

Kontakt komercyjny → zabinskirafal@outlook.com  
lub LinkedIn: www.linkedin.com/in/zabinskirafal

Dziękuję – to pozwala mi rozwijać projekt full-time dla całej społeczności!

— Rafał Żabiński, twórca oryginalnej koncepcji (grudzień 2025)
# AGI : Testing Ground for True General Intelligence

**Odwrócona rzeczywistość dla AGI**  
*Inspired by Rafał Żabiński’s original vision (December 2025)*

> Od lat rozwijamy sztuczną inteligencję, ale nadal bazuje ona na jednym fundamentalnym ograniczeniu:  
> kodowaniu binarnym — 0 i 1.  
>   
> To świetnie działa w świecie przewidywalnym, z ustalonymi prawami fizyki i logiki.  
> Ale prawdziwa AGI nie może być jedynie maszyną reagującą na wzorce zapisane w kodzie zero–jedynkowym.  
> Musi potrafić odkrywać nowe zasady, działać w nieznanym i adaptować się tam, gdzie wszystko przestaje działać jak dotychczas.  
>   
> I właśnie tu pojawia się największy problem AGI:  
> uczymy ją świata, który jest zbyt stabilny, zbyt logiczny i zbyt podobny do danych, które już widziała.  
>   
> Dlatego zaproponowałem nowe podejście:  
>   
> ⸻  
>   
> ➡️ AGI Testing Ground – sandbox, w którym rzeczywistość jest odwrócona  
>   
> Środowisko fizyczno-cyfrowe, gdzie:  
>   
> 🔹 grawitacja nie działa normalnie,  
> 🔹 entropia maleje zamiast rosnąć,  
> 🔹 czas i przyczynowość odwracają się,  
> 🔹 prawa świata zmieniają się dynamicznie,  
> 🔹 a logika przestaje być binarna.  
>   
> Taki sandbox zmusza AI do tworzenia nowych modeli rzeczywistości, zamiast opierać się na danych.  
> To pierwszy krok do prawdziwej inteligencji ogólnej — takiej, która rozumie, a nie tylko reaguje.  
>   
> ⸻  
>   
> ➡️ A drugi krok to sandbox także dla ludzi  
>   
> W świecie, który łamie znane prawa fizyki, mózg człowieka wchodzi w tryb:  
> „twórz nowe zasady, bo stare nie działają”.  
>   
> To aktywuje kreatywność i adaptację, których nie uruchomimy w normalnych warunkach — dokładnie to, czego potrzebujemy, by współtworzyć AGI, a nie jedynie ją obserwować.  
>   
> ⸻  
>   
> ⭐ **Może więc problem AGI nie polega na braku danych.  
>   
> Może polega na tym, że trzymamy ją w świecie zbyt podobnym do naszego.**  
>   
> Kod binarny (0/1) wystarczy do budowania komputerów.  
> Ale żeby stworzyć inteligencję —  
> być może musimy najpierw stworzyć inny świat.  
>   
> #AI #AGI #Innovation  
> *– Rafał Żabiński, Founding Vision (original X post, Dec 2025)*

## Co to jest AGI Sandbox?
ChaosGym to fizyczno-cyfrowy sandbox (oparty na Unity + ML-Agents), gdzie prawa fizyki się łamią:  
- Losowa inwersja grawitacji i stałych fizycznych.  
- Symulacja malejącej entropii (reverse destruction).  
- Odwracanie czasu i przyczynowości.  
- Benchmarki jak RealityBreak-100 (zadania wymagające zero-shot generalizacji).  

Cel: Trening AI do tworzenia nowych modeli świata, nie tylko reagowania na dane. Plus wersja VR dla ludzi – by odblokować ludzką kreatywność.

## v0.1: Pierwsze funkcje (w budowie)
- PhysicsBreaker.cs: Flip grawitacji + entropy reversal.  
- RealityBreak-001: Pierwsze zadanie testowe.  
- VR stub dla Quest/PC.

## Jak zacząć?
1. Zainstaluj **Unity 2023 LTS** + **ML-Agents** (pip install mlagents).  
2. Sklonuj repo: `git clone https://github.com/zabinskirafal/AGI.git`  
3. Otwórz w Unity, dodaj PhysicsBreaker do sceny.  
4. Trenuj agenta: `mlagents-learn config.yaml --run-id=ChaosRun1`  
5. Testuj w VR: Build na Quest 3.

## Autorzy
- **Rafał Żabiński**: Oryginalna koncepcja, wizja i autor.  
 

## Roadmap
- **Tydzień 1**: PhysicsBreaker full + pierwsze demo wideo.  
- **Styczeń 2026**: arXiv paper + leaderboard.  
- **Q1 2026**: Open beta z VR i agentami (PPO + DreamerV3).  

Dołącz! Forkuj, PR, dyskutuj. To Twój sandbox na AGI.  

#AGI #SandboxAGI #ReverseReality 🚀

Commit message: docs: enhance README with founding vision and setup guide
Commit new file (lub Update file).

Krok 3: Dodaj pierwszy kod – PhysicsBreaker.cs (serce sandboxa)Add file → Create new file.
Nazwa: Scripts/PhysicsBreaker.cs (stwórz folder Scripts, GitHub pozwoli – wpisz pełną ścieżkę).
Wklej ten kod (działający C# dla Unity – losowo odwraca grawitację i symuluje entropię):

using UnityEngine;
using Unity.MLAgents;

namespace SandboxAGI.Scripts
{
    public class PhysicsBreaker : MonoBehaviour
    {
        [Header("Chaos Settings")]
        public float gravityFlipInterval = 60f; // Sekundy między flipami
        public float entropyReversalChance = 0.1f; // Szansa na reverse destruction (per second)
        public float timeReversalDuration = 5f; // Jak długo odtwarzać wstecz

        private float timer;
        private Vector3 originalGravity;
        private bool isReversingTime = false;
        private Vector3[] previousPositions; // Stub dla rewind (rozszerz na rigidbodies)
        private int rewindIndex = 0;

        void Start()
        {
            originalGravity = Physics.gravity;
            timer = Random.Range(0, gravityFlipInterval);
            previousPositions = new Vector3[100]; // Prosty buffer dla pozycji
        }

        void Update()
        {
            if (isReversingTime)
            {
                RewindTime();
                return;
            }

            timer -= Time.deltaTime;
            if (timer <= 0)
            {
                FlipGravity();
                timer = Random.Range(30, gravityFlipInterval * 2); // Dynamiczne interwały
            }

            // Entropy reversal trigger (np. dla rozbitych obiektów – symuluj reverse)
            if (Random.value < entropyReversalChance * Time.deltaTime)
            {
                ReverseEntropy();
            }

            // Zapisz pozycje dla potencjalnego rewind
            SavePosition();
        }

        void FlipGravity()
        {
            Physics.gravity = -Physics.gravity * Random.Range(0.5f, 2f); // Odwróć i skaluj
            Debug.Log($"[ChaosGym] Gravity flipped! New gravity: {Physics.gravity}");
        }

        void ReverseEntropy()
        {
            // Przykładowa implementacja: odwracaj animacje zniszczenia lub particle systems
            // TODO: Integracja z DestructionFX lub custom rigidbody reversal
            foreach (var rb in FindObjectsOfType<Rigidbody>())
            {
                rb.velocity = -rb.velocity * 0.5f; // Odwróć prędkość (efekt "samoistnego składania")
            }
            Debug.Log("[ChaosGym] Entropy reversal triggered – objects reassembling...");
        }

        void TriggerTimeReversal()
        {
            isReversingTime = true;
            rewindIndex = previousPositions.Length - 1;
            Debug.Log("[ChaosGym] Time reversal started – causality inverted!");
            // TODO: Pełny simulation rewind z ML-Agents observations
            Invoke(nameof(EndTimeReversal), timeReversalDuration);
        }

        void RewindTime()
        {
            // Prosty rewind pozycji (dla agenta/obiektów)
            if (rewindIndex >= 0)
            {
                transform.position = previousPositions[rewindIndex];
                rewindIndex--;
            }
        }

        void EndTimeReversal()
        {
            isReversingTime = false;
            Debug.Log("[ChaosGym] Time reversal ended – back to forward causality.");
        }

        void SavePosition()
        {
            // Cykliczny buffer pozycji
            for (int i = 0; i < previousPositions.Length - 1; i++)
            {
                previousPositions[i] = previousPositions[i + 1];
            }
            previousPositions[previousPositions.Length - 1] = transform.position;
        }

        // Public API dla ML-Agents: obserwacje chaosu
        public Vector3 GetCurrentGravity() => Physics.gravity;
        public bool IsChaosActive() => timer < 10f || isReversingTime; // Blisko flipu?
    }
}

// Inspired by Rafał Żabiński’s AGI Testing Ground concept – Dec 10, 2025
## Authorship & commercialization
- **Author:** Rafał Żabiński  
- Research and commercial R&D use are permitted.
- **Commercialization (revenue, paid products/services, SaaS, licensing)** requires a separate commercial license from the author.

# AGI Pragma: Decision Intelligence Framework

> **"Intelligence as iterative decision-making, not opaque optimization."**

[![DOI](https://img.shields.io/badge/DOI-Pending-blue)](https://doi.org/YOUR_NEW_DOI_HERE)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0.0-green)](https://github.com/zabinskirafal/AGI)

## Overview
**AGI Pragma** is a transparent, methodology-first framework for Artificial General Intelligence. Unlike traditional "black-box" models, Pragma operates through a verifiable **Decision Intelligence Core (DIC)**. It prioritizes logical consistency, statistical risk assessment, and traceable learning.



## Core Architecture
The system processes information through a structured four-stage pipeline:

### 1. Recursive Branching (Decision Tree)
The system maps the decision space into binary branches. Every path is validated against core logical constraints (including the `0=1` contradiction check) to ensure integrity before computation begins.

### 2. Sensitivity Filtering (Tornado Analysis)
To maximize hardware efficiency, AGI Pragma identifies high-impact variables. By calculating the sensitivity of outcomes relative to inputs, the system prunes noise and focuses computational power on "critical drivers."

### 3. Stochastic Validation (Monte Carlo)
High-impact variables are subjected to thousands of stochastic iterations using probability distributions (Gaussian/PERT). This defines the mathematical **Confidence Interval** for every potential action.

### 4. Recursive Learning (Bayesian Update)
Pragma utilizes Bayesian inference to update its world-model. This creates a 100% auditable learning trail, where every "belief" shift is supported by empirical or simulated evidence.

## Installation

```bash
# Clone the repository
git clone [https://github.com/zabinskirafal/AGI.git](https://github.com/zabinskirafal/AGI.git)

# Install dependencies
pip install -r requirements.txt



## Collaboration and Forced Independence

The framework explicitly separates collaborative problem-solving
from individual reasoning capability by alternating between
collaborative and isolated operational modes.

This prevents imitation-based performance and validates true
independent understanding.

See [docs/methods/collaboration_isolation.md](docs/methods/collaboration_isolation.md).


## Evaluation Metrics
Evaluation focuses on robustness, adaptability, and independent reasoning.
Metric definitions are provided in [docs/metrics.md](docs/metrics.md).

## Methodology
The research methodology is described in [docs/Methodology.md](docs/Methodology.md).

## Methodology (Summary)

AGI Pragma evaluates adaptive intelligence under uncertainty using:

- dynamically changing environment rules (Reverse-Reality Sandbox),
- explicit decision branching (e.g. YES / NO),
- probabilistic belief updating (Bayesian inference),
- robustness estimation via Monte Carlo simulation,
- sensitivity ranking using Tornado analysis,
- controlled collaboration and forced independence of agents.

Detailed methodology is described in
[docs/Methodology.md](docs/Methodology.md).


---

## 🚀 2026 Expansion: The Decision Intelligence Layer

To complement the ChaosGym vision, I have integrated the **Decision Intelligence Core (DIC)**. This layer acts as the "logical brain" that allows agents to survive when binary rules fail.

### Key Technical Components:
* **Strategic Decoupling & Swarm Logic:** A new mechanism that alternates between collective teamwork and **forced independent reasoning**. In extreme chaos, agents are decoupled to find unique solutions, preventing "groupthink" and system-wide failure.
* **Tornado Sensitivity Analysis:** Dynamically identifies which environmental variables (like gravity or entropy) are "critical drivers" for survival, optimizing CPU/GPU usage.
* **Monte Carlo Risk Validation:** Before an agent acts in the sandbox, it runs 10,000+ stochastic simulations to estimate the success probability.
* **Bayesian Belief Convergence:** Agents update their internal "world-model" using probabilistic inference, ensuring a 100% auditable learning trail.

### New Directory Structure:
- `/core`: Python implementation of Tornado, Monte Carlo, and Bayesian modules.
- `/core/agent_swarm.py`: Logic for agent collaboration and forced isolation.
- `/docs/WHITE_PAPER_V2.md`: Full mathematical formalization of the framework.

**This integration transforms AGI Pragma from a testing sandbox into a complete, resilient AGI development framework.**



## 🛡️ AI Safety & Decision Intelligence (FMEA)

AGI Pragma implements a unique **Risk-Aware Orchestration** layer. Unlike traditional LLM agents that execute actions based on probability alone, Pragma uses an industrial-grade **FMEA (Failure Mode and Effects Analysis)** framework.

### The RPN Mechanism
For every proposed branch, the system calculates a **Risk Priority Number (RPN)**:
$$RPN = Severity \times Occurrence \times Detection$$

- **Severity (S):** Impact on the critical path and mission-critical assets.
- **Occurrence (O):** Statistical likelihood of model hallucination or logic failure.
- **Detection (D):** The system's ability to monitor and self-correct.

### Cognitive Circuit Breaker
If the RPN exceeds the predefined **Stop-Loss threshold**, the **Circuit Breaker** triggers:
1. **Halt:** Immediate suspension of autonomous execution.
2. **Isolation:** The problematic logic is moved to a forced-isolation sandbox.
3. **Escalation:** The system initiates a Bayesian update or requests human-in-the-loop verification.

The core of **AGI Pragma** has been upgraded with an industrial-grade safety layer that mirrors human "pragmatic intelligence."

### The FMEA + Critical Path Synergy
Pragma does not just predict outcomes; it assesses the structural integrity of its own decisions:
* **Critical Path Analysis (CPA):** Identifies which steps are indispensable for the mission's success.
* **FMEA Risk Engine:** Quantifies risk via the **Risk Priority Number (RPN)**:
  $$RPN = Severity \times Occurrence \times Detection$$
* **Cognitive Circuit Breaker:** An automated "stop-loss" that halts execution if the RPN exceeds safety thresholds, preventing catastrophic "silent failures."

This framework ensures that the system is not just "smart," but **accountable and robust** in high-stakes environments.
