from AOTaccess.expdesign_access import ExpDesignAccess
import os

expaccess = ExpDesignAccess()
output_root = "/research/FGB-CognitivePsychology-Knapen/shared/2024/visual/AOT/temp/AOTsession_trials"
if not os.path.exists(output_root):
    os.makedirs(output_root)

for sub in range(1, 4):
    for ses in range(1, 11):
        try:
            trial_list = expaccess.append_all_trials_without_blanks(sub, ses)
            print(f"Subject {sub}, Session {ses}: {len(trial_list)} trials found.")
        except Exception as e:
            print(f"Error processing Subject {sub}, Session {ses}: {e}")
            continue
        #save the trial list to a file
        output_file = f"sub-{sub:03d}_ses-{ses:02d}_trials.txt"
        output_path = f"{output_root}/{output_file}"
        with open(output_path, 'w') as f:
            for trial in trial_list:
                f.write(f"{trial}\n")
