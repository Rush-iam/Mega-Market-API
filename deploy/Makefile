#                                              _        _
#   /\/\   ___  __ _  __ _    /\/\   __ _ _ __| | _____| |_
#  /    \ / _ \/ _` |/ _` |  /    \ / _` | '__| |/ / _ \ __|
# / /\/\ \  __/ (_| | (_| | / /\/\ \ (_| | |  |   <  __/ |_
# \/    \/\___|\__, |\__,_| \/    \/\__,_|_|  |_|\_\___|\__|
#              |___/                     by nGragas/Rush-iam

NAME = mega_market

up:
	docker compose -p "$(NAME)" --env-file ../project/config.env up --build
clean:
	docker compose -p "$(NAME)" down --rmi all -v -t 3

.PHONY: up clean
