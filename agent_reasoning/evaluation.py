def get_patch_files(patch):
    files = set()
    for line in patch.splitlines():
        if line.startswith('+++ ') or line.startswith('--- '):
            file_name = line[6:]
            files.add(file_name)
    return files

def get_files(example):
    files = set()
    files.update(get_patch_files(example['patch']))
    files.update(get_patch_files(example['test_patch']))
    return list(files)

class FileResults:
    def __init__(self, true_positives, false_positives, false_negatives):
        self.true_positives = true_positives
        self.false_positives = false_positives
        self.false_negatives = false_negatives

    def exclude_matches(self, results):
        return FileResults(
            self.true_positives,
            self.false_positives - results.true_positives,
            self.false_negatives,
        )

    def precision(self):
        return len(self.true_positives) / max(1, len(self.true_positives) + len(self.false_positives))

    def recall(self):
        return len(self.true_positives) / max(1, len(self.true_positives) + len(self.false_negatives))
    
    def to_json(self):
        return {
            "true_positives": list(self.true_positives),
            "false_positives": list(self.false_positives),
            "false_negatives": list(self.false_negatives),
        }

def match_files(response_files, target_files):
    true_positives = set(response_files) & set(target_files)
    false_positives = set(response_files) - set(target_files)
    false_negatives = set(target_files) - set(response_files)
    return FileResults(true_positives, false_positives, false_negatives)

