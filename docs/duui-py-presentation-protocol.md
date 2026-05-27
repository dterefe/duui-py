# DUUI-Py Presentation Protocol

## Objective

Create a Jupyter notebook for a presentation on DUUI-Py as a master-level computer science research project. The notebook must describe the evolution from annotator-author ergonomics to event telemetry and the experimental descriptor-generated MsgPack/Lua codec, then analyze baseline-versus-async evaluations for spaCy, TaxoNERD, GNFinder, and Gazetteer.

## Writing Constraints

- Write in neutral research-paper English.
- Phrase the work anonymously and from the perspective of a student research project, without fourth-wall remarks.
- Do not claim behavior that has not been directly checked in code, data, reports, or cited sources.
- Use the names `baseline` and `async variants` in evaluation sections; avoid improvised naming conventions.
- Prefer evidence tables and plots over unsupported interpretation.

## Report Structure

1. Motivation and timeline:
   - DUUI-Py was introduced to reduce DUUI Java v1 annotator boilerplate.
   - Python was chosen because annotator authors commonly use Python NLP libraries.
2. Managed annotator boilerplate:
   - Ready-made server endpoints.
   - UIMA type-system data structures.
   - Configuration and descriptor ergonomics.
3. `v2/events`:
   - Logging levels.
   - Telemetry and metrics.
   - Error handling.
   - Asynchronous streaming without process-path overhead.
4. Codecs and adapters:
   - Backwards-compatible migration for custom Lua scripts.
   - Descriptor-generated Lua.
   - Annotator descriptor structure and examples verified from code.
   - Serialization/deserialization generation.
   - MsgPack evidence versus JSON.
   - Wire/chunking structure.
   - Abstract HTTP streaming and pipelining motivation.
5. Evaluation:
   - Hypotheses.
   - Initial bottlenecks: Pydantic background activity and transport object footprint.
   - spaCy: detailed procedural latency/throughput/resource analysis.
   - TaxoNERD: detailed procedural latency/throughput/resource analysis.
   - GNFinder and Gazetteer: generality and ergonomics with result plots.

## Evidence Rules

- Confirm code behavior with local file references before writing.
- Confirm metrics from CSV, JSON, notebook outputs, or evaluation reports before plotting.
- Use citations for external claims about visualization, MessagePack/JSON, streaming, and telemetry.
- Show latency distributions, tail latency, throughput, and resource footprints where data exists.
- If data is absent for a requested plot, state that it is absent in the notebook rather than fabricating it.

## Resume Point

After Git cleanup, continue by inventorying available evaluation artifacts, then create the notebook with executable data-loading cells and Markdown analysis cells.
