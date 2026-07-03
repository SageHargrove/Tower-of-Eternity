import json
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
generated_file = os.path.join(backend_dir, "generated_skills.json")
service_file = os.path.join(os.path.dirname(backend_dir), "services", "skills_service.py")

with open(generated_file, "r") as f:
    data = json.load(f)

with open(service_file, "r") as f:
    lines = f.readlines()

out_lines = []
in_skill_pool = False
for line in lines:
    if line.startswith("SKILL_POOL = {"):
        out_lines.append(line)
        in_skill_pool = True
        
        # Inject the new skills immediately after the opening brace
        for class_data in data:
            cname = class_data["class_name"]
            skills_str = json.dumps(class_data["skills"], indent=8)
            out_lines.append(f'    "{cname}": {skills_str},\n')
            
    elif in_skill_pool:
        if line.startswith("}"):
            # Done skipping old contents
            in_skill_pool = False
            out_lines.append(line)
    else:
        out_lines.append(line)

with open(service_file, "w") as f:
    f.writelines(out_lines)

print(f"Injected {len(data)} classes into skills_service.py!")
