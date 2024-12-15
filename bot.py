import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import time
import random


VK_TOKEN = vk1.a.sFi4xCpReOQkbp3zVy5OY7gFWy-1vgRjoWDyGmOGZFzOoAG0lnvJh4lCJF1E3gYcJEp2MW4ciBz-zx0yfTAT11EvVd-8E2MKmMJdL-MK6PRo543x6ME2Khb7C8xR3X9LCcYfqJpiBNFL-rGfwCpvI3sRdHDKLyxqXchkvpBCtMKFOEQlpTMTKqKcP1wBMBU9FOsxZq-8iQsZgDbusM7c-Q


CHAT_ID = 153


MIN_PLAYERS = 5
game_state = {
    "status": "idle",     
    "players": [],
    "roles": {},
    "admin_id": None,
    "votes": {},
    "round": 0
}

def send_message_to_chat(chat_id, text):
    vk.messages.send(
        peer_id=2000000000 + chat_id,
        message=text,
        random_id=0
    )

def send_message_to_user(user_id, text):
    vk.messages.send(
        user_id=user_id,
        message=text,
        random_id=0
    )

def assign_roles(players):
    
    num_virus = max(1, len(players)//4)
    roles_list = ["VIRUS"] * num_virus + ["Service"] * (len(players) - num_virus)
    random.shuffle(roles_list)
    return dict(zip(players, roles_list))

def reset_game():
    game_state["status"] = "idle"
    game_state["players"] = []
    game_state["roles"] = {}
    game_state["admin_id"] = None
    game_state["votes"] = {}
    game_state["round"] = 0

def start_game():
    game_state["roles"] = assign_roles(game_state["players"])
    game_state["status"] = "started"
    game_state["round"] = 1
    
    for pid, role in game_state["roles"].items():
        send_message_to_user(pid, f"Ваша роль: {role}. Не разглашайте её!")
    send_message_to_chat(CHAT_ID, "Все роли розданы, игра начинается!")
    start_round()

def start_round():
    game_state["round"] = 1
    send_message_to_chat(CHAT_ID, f"Раунд {game_state['round']}. Обсуждайте в течение 30 секунд, кто может быть предателем.")
    
    time.sleep(30)
    go_to_voting()

def go_to_voting():
    game_state["status"] = "voting"
    send_message_to_chat(CHAT_ID, "Время голосовать! Напишите команду в чате: !vote @idXXXX")
    

def end_voting():
    tally = {}
    for voter, voted in game_state["votes"].items():
        tally[voted] = tally.get(voted, 0) + 1

    if not tally:
        send_message_to_chat(CHAT_ID, "Никто не проголосовал. Странно...")
    else:
        max_votes = max(tally.values())
        suspects = [p for p, vcount in tally.items() if vcount == max_votes]
        virus_found = any(game_state["roles"].get(s) == "VIRUS" for s in suspects)
        
        if virus_found:
            send_message_to_chat(CHAT_ID, "Предателя нашли! Service побеждают!")
        else:
            send_message_to_chat(CHAT_ID, "Промахнулись! VIRUS побеждают!")

    
    roles_info = "Роли были следующие:\n"
    for pid, role in game_state["roles"].items():
        roles_info += f"id{pid}: {role}\n"
    send_message_to_chat(CHAT_ID, roles_info)
    reset_game()


vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)


for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        text = event.text.strip().lower()
        peer_id = event.peer_id

        
        if peer_id > 2000000000:
            
            chat_id = peer_id - 2000000000

            
            if text == "!start_game" and game_state["status"] == "idle":
                game_state["status"] = "gathering"
                game_state["admin_id"] = user_id
                send_message_to_chat(chat_id, "Начинаем набор игроков! Чтобы участвовать, введите !join")

            elif text == "!join" and game_state["status"] == "gathering":
                if user_id not in game_state["players"]:
                    game_state["players"].append(user_id)
                    send_message_to_chat(chat_id, f"Игрок id{user_id} присоединился. Всего игроков: {len(game_state['players'])}")

            elif text == "!begin" and game_state["status"] == "gathering":
                if len(game_state["players"]) >= MIN_PLAYERS:
                    send_message_to_chat(chat_id, "Достаточно игроков! Игра начинается!")
                    start_game()
                else:
                    send_message_to_chat(chat_id, f"Недостаточно игроков. Нужно минимум {MIN_PLAYERS}.")

            elif text.startswith("!vote") and game_state["status"] == "voting":
                parts = text.split()
                if len(parts) == 2:
                    target_str = parts[1].replace("[", "").replace("]", "").replace("@", "")
                    # Ожидаем формат типа @idXXXX
                    if "id" in target_str:
                        target_id_str = target_str.replace("id", "").split("|")[0]
                        try:
                            target_id = int(target_id_str)
                            if target_id in game_state["players"]:
                                game_state["votes"][user_id] = target_id
                                send_message_to_chat(chat_id, f"Игрок id{user_id} проголосовал за id{target_id}.")
                                
                            else:
                                send_message_to_chat(chat_id, "Такого игрока нет в списке участников.")
                        except ValueError:
                            send_message_to_chat(chat_id, "Неверный формат ID.")
                    else:
                        send_message_to_chat(chat_id, "Неверный формат команды !vote. Используйте !vote @idXXXX")

            
            elif text == "!end_voting" and game_state["status"] == "voting":
                end_voting()

        else:
            
            if text == "!help":
                send_message_to_user(user_id, "Команды доступны в беседе.")

