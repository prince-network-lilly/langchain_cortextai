"""Batch processing — run inputs through chains efficiently in batches."""

import time
from typing import Any, Callable, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


class BatchProcessor:
    """Process multiple inputs through a chain/function with progress tracking.

    Usage:
        processor = BatchProcessor(chain, max_workers=4, verbose=True)
        results = processor.run(["input1", "input2", "input3"])
    """

    def __init__(
        self,
        chain_or_fn: Any,
        max_workers: int = 1,
        batch_size: int = 10,
        delay_between_calls: float = 0.0,
        verbose: bool = False,
        on_error: str = "continue",  # "continue", "stop", "retry"
        max_retries: int = 2,
    ):
        self.chain_or_fn = chain_or_fn
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.delay = delay_between_calls
        self.verbose = verbose
        self.on_error = on_error
        self.max_retries = max_retries

    def _process_single(self, input_item: Any, index: int) -> Dict:
        """Process a single input item."""
        start = time.time()
        for attempt in range(self.max_retries + 1):
            try:
                if callable(self.chain_or_fn):
                    if isinstance(input_item, dict):
                        result = self.chain_or_fn(input_item)
                    else:
                        result = self.chain_or_fn({"input": str(input_item)})
                elif hasattr(self.chain_or_fn, "invoke"):
                    if isinstance(input_item, dict):
                        result = self.chain_or_fn.invoke(input_item)
                    else:
                        result = self.chain_or_fn.invoke({"input": str(input_item)})
                elif hasattr(self.chain_or_fn, "run"):
                    result = {"output": self.chain_or_fn.run(str(input_item))}
                else:
                    result = {"output": str(self.chain_or_fn(input_item))}

                elapsed = time.time() - start
                return {
                    "index": index,
                    "input": input_item,
                    "output": result,
                    "status": "success",
                    "duration": round(elapsed, 3),
                    "attempts": attempt + 1,
                }
            except Exception as e:
                if attempt == self.max_retries or self.on_error == "stop":
                    elapsed = time.time() - start
                    return {
                        "index": index,
                        "input": input_item,
                        "output": None,
                        "status": "error",
                        "error": str(e),
                        "duration": round(elapsed, 3),
                        "attempts": attempt + 1,
                    }
                time.sleep(1)  # Brief pause before retry

    def run(self, inputs: List[Any]) -> "BatchResult":
        """Process all inputs and return a BatchResult."""
        results = []
        total = len(inputs)
        start_time = time.time()

        if self.verbose:
            print(f"[Batch] Processing {total} items (workers={self.max_workers})...")

        if self.max_workers <= 1:
            # Sequential processing
            for i, item in enumerate(inputs):
                result = self._process_single(item, i)
                results.append(result)
                if self.verbose and (i + 1) % max(1, total // 10) == 0:
                    print(f"  [{i + 1}/{total}] {result['status']}")
                if self.delay > 0:
                    time.sleep(self.delay)
                if result["status"] == "error" and self.on_error == "stop":
                    break
        else:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._process_single, item, i): i for i, item in enumerate(inputs)}
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    if self.verbose:
                        done = len(results)
                        print(f"  [{done}/{total}] item {result['index']}: {result['status']}")

        # Sort by original index
        results.sort(key=lambda r: r["index"])
        elapsed = time.time() - start_time

        if self.verbose:
            success = sum(1 for r in results if r["status"] == "success")
            print(f"[Batch] Done: {success}/{total} succeeded in {elapsed:.1f}s")

        return BatchResult(results=results, total_duration=elapsed)


class BatchResult:
    """Container for batch processing results with helper methods."""

    def __init__(self, results: List[Dict], total_duration: float):
        self.results = results
        self.total_duration = total_duration

    @property
    def successes(self) -> List[Dict]:
        return [r for r in self.results if r["status"] == "success"]

    @property
    def failures(self) -> List[Dict]:
        return [r for r in self.results if r["status"] == "error"]

    @property
    def outputs(self) -> List[Any]:
        """Get just the outputs (None for failures)."""
        return [r["output"] for r in self.results]

    @property
    def success_rate(self) -> float:
        if not self.results:
            return 0.0
        return len(self.successes) / len(self.results)

    def summary(self) -> str:
        return (
            f"Batch: {len(self.successes)}/{len(self.results)} succeeded "
            f"({self.success_rate:.1%}) in {self.total_duration:.1f}s"
        )

    def __len__(self) -> int:
        return len(self.results)

    def __getitem__(self, index):
        return self.results[index]

    def __repr__(self) -> str:
        return self.summary()
