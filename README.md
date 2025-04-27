# How to use

## ✅ Summary

| Mode | Description | Config Field |
|:----|:------------|:-------------|
| 1 | Continuous monitoring | None |
| 2 | Process a list of commits | `commit_list` |
| 3 | Compare two commits | `compare_pair` |


## Type of Usage:
1. Monitor all commits since `start_commit`:
2. Specify a list of aiter commits to check in order. After finishing the list, it will continue normal monitoring.
```json
...
"commit_list": [
    "commit_hash1",
    "commit_hash2",
    "commit_hash3"
]
...
```
3. Compare two specific commits only. Script will exit after comparison.
```json
...
"compare_pair": [
    "old_commit_hash",
    "new_commit_hash"
]
...
``` 


## Usage Method 1:

1. Fork this repository. Then git clone the repository.

2. Create a file named `aiter_api_watcher_config.json` using `template_to_initialize_aiter_api_watcher_config.json`.

3. Run the following command: (replace the GITHUB_TOKEN with your GITHUB token)
```
   docker run -it \
      --network=host \
      --group-add=video \
      --ipc=host \
      --cap-add=SYS_PTRACE \
      --security-opt seccomp=unconfined \
      --device /dev/kfd \
      --device /dev/dri \
      -e GITHUB_TOKEN=$GITHUB_TOKEN \
      -v /path/to/script/directory/aiter-api-watcher:/app/aiter-api-watcher \
      rocm/vllm-dev:base \
      bash -c "cd /app/aiter-api-watcher && python3 aiter_api_watcher.py"
```


4. The aiter_api_watcher.py will generates a log to `aiter_api_watcher.log`.

Example content of the `aiter_api_watcher.log`:

```text
2025-04-26 17:41:54,547 - aiter_api_watcher - INFO - Starting aiter API watcher
2025-04-26 17:41:54,547 - aiter_api_watcher - INFO - Monitoring 4 functions
2025-04-26 17:41:54,547 - aiter_api_watcher - INFO - Check interval: 3600 seconds
2025-04-26 17:41:54,547 - aiter_api_watcher - INFO - Checking for API changes...
2025-04-26 17:41:55,733 - aiter_api_watcher - INFO - Found 7 new commits since 365bd25a3f97673b291bc42f1459fbb51bf1c634
2025-04-26 17:41:55,733 - aiter_api_watcher - INFO - Checking commit f39b7a4221c8a5d5f1bcb408ac13a3d7d9f00f8e
2025-04-26 17:41:55,737 - aiter_api_watcher - INFO - Cloning repository for commit f39b7a4221c8a5d5f1bcb408ac13a3d7d9f00f8e
2025-04-26 17:41:58,654 - aiter_api_watcher - INFO - Checking out commit f39b7a4221c8a5d5f1bcb408ac13a3d7d9f00f8e
2025-04-26 17:41:58,730 - aiter_api_watcher - INFO - Updating submodules
2025-04-26 17:41:59,057 - aiter_api_watcher - INFO - Installing aiter package
2025-04-26 17:42:11,846 - aiter_api_watcher - INFO - Successfully installed aiter
2025-04-26 17:42:31,497 - aiter_api_watcher - INFO - Initial signature for fmoe_fp8_blockscale_g1u1: (out: torch.Tensor, input: torch.Tensor, gate: torch.Tensor, down: torch.Tensor, sorted_token_ids: torch.Tensor, sorted_weights: torch.Tensor, sorted_expert_ids: torch.Tensor, num_valid_ids: torch.Tensor, topk: int, input_scale: torch.Tensor, fc1_scale: torch.Tensor, fc2_scale: torch.Tensor, fc_scale_blkn: int = 128, fc_scale_blkk: int = 128, fc2_smooth_scale: Optional[torch.Tensor] = None, activation: module_aiter_enum.ActivationType = <ActivationType.Silu: 0>)
2025-04-26 17:42:44,422 - aiter_api_watcher - INFO - Initial signature for rocm_aiter_asm_fmoe.moe_sorting_ck: (topk_ids, topk_weights, num_experts, model_dim, moebuf_dtype, block_size=32, expert_mask=None)
2025-04-26 17:42:57,457 - aiter_api_watcher - INFO - Initial signature for rocm_aiter_asm_fmoe.asm_moe: (hidden_states, w1, w2, topk_weight, topk_ids, fc1_scale=None, fc2_scale=None, fc1_smooth_scale=None, fc2_smooth_scale=None, a16=False, per_tensor_quant_scale=None, expert_mask=None, activation=<ActivationType.Silu: 0>)
2025-04-26 17:43:10,474 - aiter_api_watcher - INFO - Initial signature for ck_moe_2stages: (a1, w1, w2, topk_weight, topk_ids, fc1_scale=None, fc2_scale=None, a1_scale=None, a2_scale=None, block_size=None, expert_mask=None)
2025-04-26 17:43:10,896 - aiter_api_watcher - INFO - Checking commit 70ae241a4d58ce4c05ab6e9ba37838923623e2b5
2025-04-26 17:43:10,902 - aiter_api_watcher - INFO - Cloning repository for commit 70ae241a4d58ce4c05ab6e9ba37838923623e2b5
2025-04-26 17:43:13,883 - aiter_api_watcher - INFO - Checking out commit 70ae241a4d58ce4c05ab6e9ba37838923623e2b5
2025-04-26 17:43:13,959 - aiter_api_watcher - INFO - Updating submodules
2025-04-26 17:43:14,284 - aiter_api_watcher - INFO - Installing aiter package
2025-04-26 17:43:27,050 - aiter_api_watcher - INFO - Successfully installed aiter
2025-04-26 17:43:46,873 - aiter_api_watcher - INFO - No API change for fmoe_fp8_blockscale_g1u1
2025-04-26 17:43:59,833 - aiter_api_watcher - INFO - No API change for rocm_aiter_asm_fmoe.moe_sorting_ck
2025-04-26 17:44:12,809 - aiter_api_watcher - INFO - No API change for rocm_aiter_asm_fmoe.asm_moe
2025-04-26 17:44:25,779 - aiter_api_watcher - INFO - No API change for ck_moe_2stages
2025-04-26 17:44:26,190 - aiter_api_watcher - INFO - Checking commit 11c3b4447033f6fecc532336ad38e759745d6192
2025-04-26 17:44:26,194 - aiter_api_watcher - INFO - Cloning repository for commit 11c3b4447033f6fecc532336ad38e759745d6192
2025-04-26 17:44:29,264 - aiter_api_watcher - INFO - Checking out commit 11c3b4447033f6fecc532336ad38e759745d6192
2025-04-26 17:44:29,342 - aiter_api_watcher - INFO - Updating submodules
2025-04-26 17:44:29,620 - aiter_api_watcher - INFO - Installing aiter package
2025-04-26 17:44:42,497 - aiter_api_watcher - INFO - Successfully installed aiter
2025-04-26 17:45:02,308 - aiter_api_watcher - INFO - No API change for fmoe_fp8_blockscale_g1u1
2025-04-26 17:45:15,259 - aiter_api_watcher - INFO - No API change for rocm_aiter_asm_fmoe.moe_sorting_ck
2025-04-26 17:45:28,299 - aiter_api_watcher - INFO - No API change for rocm_aiter_asm_fmoe.asm_moe
2025-04-26 17:45:41,415 - aiter_api_watcher - INFO - No API change for ck_moe_2stages
2025-04-26 17:45:41,815 - aiter_api_watcher - INFO - Checking commit 54c542c97e8eb38d34ae6cb6282d9a9e7a132411
2025-04-26 17:45:41,820 - aiter_api_watcher - INFO - Cloning repository for commit 54c542c97e8eb38d34ae6cb6282d9a9e7a132411
2025-04-26 17:45:44,841 - aiter_api_watcher - INFO - Checking out commit 54c542c97e8eb38d34ae6cb6282d9a9e7a132411
2025-04-26 17:45:44,914 - aiter_api_watcher - INFO - Updating submodules
2025-04-26 17:45:45,229 - aiter_api_watcher - INFO - Installing aiter package
2025-04-26 17:45:57,837 - aiter_api_watcher - INFO - Successfully installed aiter
2025-04-26 17:46:17,341 - aiter_api_watcher - INFO - No API change for fmoe_fp8_blockscale_g1u1
2025-04-26 17:46:30,248 - aiter_api_watcher - INFO - No API change for rocm_aiter_asm_fmoe.moe_sorting_ck
2025-04-26 17:46:43,169 - aiter_api_watcher - INFO - No API change for rocm_aiter_asm_fmoe.asm_moe
2025-04-26 17:46:56,131 - aiter_api_watcher - INFO - No API change for ck_moe_2stages
2025-04-26 17:46:56,538 - aiter_api_watcher - INFO - Checking commit 54d0ac15b61f1d8295b2b75362c84ec2fe946b54
2025-04-26 17:46:56,542 - aiter_api_watcher - INFO - Cloning repository for commit 54d0ac15b61f1d8295b2b75362c84ec2fe946b54
2025-04-26 17:46:59,554 - aiter_api_watcher - INFO - Checking out commit 54d0ac15b61f1d8295b2b75362c84ec2fe946b54
2025-04-26 17:46:59,808 - aiter_api_watcher - INFO - Updating submodules
2025-04-26 17:46:59,903 - aiter_api_watcher - INFO - Installing aiter package
2025-04-26 17:47:12,568 - aiter_api_watcher - INFO - Successfully installed aiter
2025-04-26 17:47:32,088 - aiter_api_watcher - INFO - No API change for fmoe_fp8_blockscale_g1u1
2025-04-26 17:47:45,163 - aiter_api_watcher - INFO - No API change for rocm_aiter_asm_fmoe.moe_sorting_ck
2025-04-26 17:47:58,255 - aiter_api_watcher - INFO - No API change for rocm_aiter_asm_fmoe.asm_moe
```

## Usage Method 2:
Follow the steps in Usage Method 1, with the following changes:

1. Specify a list of aiter commits to check in order. After finishing the list, it will continue normal monitoring.
```json
...
"commit_list": [
    "commit_hash1",
    "commit_hash2",
    "commit_hash3"
]
...
```

Run the command as in Usage Method 1.

## Usage Method 2:
Follow the steps in Usage Method 1, with the following changes:

1. Specify a list of aiter commits to check in order. After finishing the list, it will continue normal monitoring.
```json
...
"compare_pair": [
    "old_commit_hash",
    "new_commit_hash"
]
...
```

Example console logs:
```console
...
2025-04-27 15:23:42,995 - aiter_api_watcher - INFO - No API change for gemm_a8w8_CK between 365bd25a3f97673b291bc42f1459fbb51bf1c634 and 28ceb1e2299c904229af0e45c38dde0efa7d14fb
2025-04-27 15:23:56,000 - aiter_api_watcher - INFO - No API change for shuffle_weight between 365bd25a3f97673b291bc42f1459fbb51bf1c634 and 28ceb1e2299c904229af0e45c38dde0efa7d14fb
2025-04-27 15:23:56,449 - aiter_api_watcher - INFO - Exiting after comparing two commits
```

Example logs:
```text
2025-04-27 15:22:28,295 - aiter_api_watcher - INFO - Starting aiter API watcher
2025-04-27 15:22:28,295 - aiter_api_watcher - INFO - Monitoring 2 functions
2025-04-27 15:22:28,295 - aiter_api_watcher - INFO - Check interval: 3600 seconds
2025-04-27 15:22:28,295 - aiter_api_watcher - INFO - Checking for API changes...
2025-04-27 15:22:28,295 - aiter_api_watcher - INFO - Comparing two commits: 365bd25a3f97673b291bc42f1459fbb51bf1c634 -> 28ceb1e2299c904229af0e45c38dde0efa7d14fb
2025-04-27 15:23:42,995 - aiter_api_watcher - INFO - No API change for gemm_a8w8_CK between 365bd25a3f97673b291bc42f1459fbb51bf1c634 and 28ceb1e2299c904229af0e45c38dde0efa7d14fb
2025-04-27 15:23:56,000 - aiter_api_watcher - INFO - No API change for shuffle_weight between 365bd25a3f97673b291bc42f1459fbb51bf1c634 and 28ceb1e2299c904229af0e45c38dde0efa7d14fb
2025-04-27 15:23:56,449 - aiter_api_watcher - INFO - Exiting after comparing two commits
```

