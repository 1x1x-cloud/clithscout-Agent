import json
from pathlib import Path

root = Path('D:/clothscout').resolve()
registry_file = root / 'project_governance/workspace_registry/config/modules.json'
registry = json.loads(registry_file.read_text(encoding='utf-8'))
index_file = root / 'project_governance/workspace_registry/docs/MODULE_INDEX.md'
index = index_file.read_text(encoding='utf-8')
for module in registry:
    old_row = '| ' + module['core_module'] + ' | ' + module['purpose'] + ' | ' + '、'.join(module['submodules']) + ' |'
    module['submodules'] = sorted(p.name for p in (root / module['core_module']).iterdir() if p.is_dir())
    new_row = '| ' + module['core_module'] + ' | ' + module['purpose'] + ' | ' + '、'.join(module['submodules']) + ' |'
    assert old_row in index
    index = index.replace(old_row, new_row)
registry_file.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding='utf-8')
index_file.write_text(index, encoding='utf-8')
state_file = root / 'project_governance/project_state/docs/TASK_STATE.md'
state = state_file.read_text(encoding='utf-8')
old = '[selection-agent-website/TASK_STATE.md](../selection-agent-website/TASK_STATE.md)'
external = Path('C:/Users/86130/Documents/ChatGPT/yuans/selection-agent-website/TASK_STATE.md')
assert external.is_file() and old in state
state_file.write_text(state.replace(old, '[原工作区保留的网站子项目状态](' + external.as_posix() + ')'), encoding='utf-8')
print(json.dumps({'core_modules': len(registry), 'submodules': sum(len(m['submodules']) for m in registry)}, ensure_ascii=False))
