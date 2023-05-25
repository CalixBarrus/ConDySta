import os

from hybrid_config import HybridAnalysisConfig


def clean(config: HybridAnalysisConfig):
    flowdroid_first_pass_logs_path = config.flowdroid_first_pass_logs_path
    flowdroid_second_pass_logs_path = config.flowdroid_second_pass_logs_path

    for folder in [flowdroid_first_pass_logs_path, flowdroid_second_pass_logs_path]:
        cmd = f'rm {os.path.join(folder, "*.log")}'
        print(cmd)
        os.system(cmd)
