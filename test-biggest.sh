rm -rf ./people/*
rm -rf ./errors/*
rm out.txt
python migrate.py tina.foley >> out.txt
python migrate.py mary.juno >> out.txt
python migrate.py gordon.haramaki >> out.txt
python migrate.py mary.poffenroth >> out.txt
python migrate.py monika.kress >> out.txt
python migrate.py olenka.hubickyjcabot >> out.txt
python migrate.py shantanu.phukan >> out.txt
python migrate.py james.lee >> out.txt
python migrate.py lui.lam >> out.txt
python migrate.py paula.jefferis-nilsen >> out.txt
cd people
zip -r archive.zip *
