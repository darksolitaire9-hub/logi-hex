# Logi-Hex Software Design Document (SDD)

## Core Philosophy
This document is the absolute "Bible" for the Logi-Hex architecture. All code changes must conform to these design patterns. If a proposed change violates these rules, the developer (Human or AI) must rethink the approach.

## 1. Architecture & Tech Stack
Logi-Hex is a local-first inventory and forecasting system.
- **Frontend**: Vue.js 3 (Composition API), Nuxt 3, NuxtUI, TailwindCSS.
- **Backend / Desktop**: Tauri v2, Rust.
- **Database**: Local SQLite database (`logihex.db`), accessed exclusively via Rust.
- **Data Sovereignty**: The application must never rely on cloud synchronization or external servers for core functionality. 

## 2. UI/UX Component Decoupling
We strictly enforce the "Smart vs. Dumb" component pattern to maintain testability and UI purity.
- **Container Components (Smart)**: Examples include `MovementSlideover.vue`. These components manage state, talk to composables (e.g., `useLedger`), invoke Tauri commands, and handle error UI. They contain NO complex HTML layout.
- **Presentational Components (Dumb)**: Examples include `MovementForm.vue`. These components take data in via `props` and emit events via `defineEmits`. They have zero awareness of the database, Tauri invokes, or global state.

## 3. Data Flow & Gravity
- **Rust is the Source of Truth**: All heavy mathematical computations, time-series gap filling, and machine learning inferences must happen in Rust.
- **The Frontend is a Thin Client**: The Vue frontend should only concern itself with data binding and UI/UX state. It must not process complex aggregations or data masking.

## 4. Forecasting Rules (Negative Space)
- **Predict Demand, Not Net Stock**: Forecasting engines must predict pure outflow (usage/demand), explicitly filtering out manual restocks or corrections.
- **No Hallucinated Demand**: Days with 0 inventory and 0 usage must be treated as "Censored Demand" and linearly interpolated, NOT treated as days where nobody wanted the item.
- **No Python Sidecars**: AI Forecasting is executed natively in Rust (via ONNX bindings or mathematical models like Croston) to prevent zombie processes and dependency hell.

## 5. Development Workflow
- **Graphify**: We rely on a Graphify-generated knowledge graph for accurate codebase context. Developers must consult `graphify-out/` before making architectural assumptions.
