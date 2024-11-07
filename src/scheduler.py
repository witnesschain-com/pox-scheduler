from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess

# Function to execute the second script
def execute_challenge_script(
                config_file='config/config.json',
                proof_type='pob',
                challenger_count=2,
                private_key='',
                prover=''
    ):
    print("Called script")
    try:
        # Run the second script using subprocess
        subprocess.run(
                        ["python", "run_challenge.py",
                        "--config_file",config_file,
                        "--proof_type",proof_type,
                        "--challenger_count",challenger_count,
                        "--private_key",private_key,
                        "--prover",prover,
                        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing script: {e}")

# Create a scheduler
scheduler = BlockingScheduler()

# Schedule the job to run every minute or any schedule you prefer
config_file,proof_type,challenger_count,private_key,prover = ['config/config.json','pol',"2",'0xdf4caa61d929f89e824e3cebb7ef62891acecbb0e12b4c22beee7c91a34a7e9c','']

provers = [
]
for prover in provers:
    scheduler.add_job(execute_challenge_script, 'interval', minutes=5,args=[config_file,proof_type,challenger_count,private_key,prover])

# Start the scheduler
if __name__ == "__main__":
    try:
        print("Scheduler started. Running script every 5 minutes...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
