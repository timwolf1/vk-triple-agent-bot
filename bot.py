import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import random
import time


VK_TOKEN = vk1.a.WT25RMfKt-mcWO5HCGEcgWTF9PLvUJDiFfhBHdhDGBCbaNud-Jy3wfGdfjMZSTpsv1AgAMYkoLylAUBegeRgDzfMrKH1tupcwhIcv-xyW8mb0tSW1vddwGKFK65lWbAHQ5tOihP1Es7gQH_WRYZxC2AyLQvfrz1fesJkdhGDtO9ykAcg7b_4vAikbT6KlZ6jRvSiZ8JQc5CA-Yar9P_PeQ

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)


CHAT_ID = c2

game_state = {
    "status": "idle",     # idle | gathering | started | voting | ended
    "players": [],         # список участников user_id
    "roles": {},           # user_id -> "Service" или "VIRUS"
    "admin_id": None,
    "votes": {},
    "round": 0
}

MIN_PLAYERS = 5

def send_message_to_user(user_id, text):
    vk.messages.send(
        user_id=user_id,
        message=text,
        random_id=0
    )

def send_message_to_chat(chat_id, text):
    vk.messages.send(
        peer_id=2000000000 + chat_id,
        message=text,
        random_id=0
    )

def assign_roles(players):
    num_virus = max(1, len(players)//4)
    roles_list = ["VIRUS"] * num_virus + ["Service"] * (len(players)-num_virus)
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
        send_message_to_user(pid, f"Ваша роль: {role}")

    
    start_round()

def start_round():
    send_message_to_chat(CHAT_ID, f"Начинается раунд {game_state['round']}! Обсуждайте, кто предатель.")
    # Для примера подождём 10 секунд и сразу пойдём к голосованию
    # В реальной игре вы можете сделать таймер или ручной переход по команде админа
    time.sleep(50)
    go_to_voting()

def go_to_voting():
    game_state["status"] = "voting"
    send_message_to_chat(CHAT_ID, "Время голосовать! Напишите команду !vote @idXXXX")

def end_voting():
    tally = {}
    for voter, voted in game_state["votes"].items():
        tally[voted] = tally.get(voted, 0) + 1
    
    if not tally:
        send_message_to_chat(CHAT_ID, "Никто не проголосовал. Это странно...")
    else:
        max_votes = max(tally.values())
        suspects = [p for p, vcount in tally.items() if vcount == max_votes]
        virus_found = any(game_state["roles"].get(s) == "VIRUS" for s in suspects)
        
        if virus_found:
            send_message_to_chat(CHAT_ID, "Предателя нашли! Service выигрывают!")
        else:
            send_message_to_chat(CHAT_ID, "Вы ошиблись! VIRUS побеждают!")
    
    
    role_text = "Роли были:\n"
    for pid, role in game_state["roles"].items():
        role_text += f"id{pid}: {role}\n"
    send_message_to_chat(CHAT_ID, role_text)
    reset_game()

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
                send_message_to_chat(chat_id, "Начался набор игроков! Введите !join чтобы участвовать.")

            elif text == "!join" and game_state["status"] == "gathering":
                if user_id not in game_state["players"]:
                    game_state["players"].append(user_id)
                    send_message_to_chat(chat_id, f"Игрок id{user_id} добавлен. Всего: {len(game_state['players'])}")

            elif text == "!begin" and game_state["status"] == "gathering":
                if len(game_state["players"]) >= MIN_PLAYERS:
                    send_message_to_chat(chat_id, "Игра начинается!")
                    start_game()
                else:
                    send_message_to_chat(chat_id, f"Недостаточно игроков. Нужно минимум {MIN_PLAYERS}.")

            
            if text.startswith("!vote") and game_state["status"] == "voting":
                parts = text.split()
                if len(parts) == 2:
                    target_str = parts[1].replace("@","").replace("[","").replace("]","")
                    
                    if "id" in target_str:
                        target_id_str = target_str.replace("id","").split("|")[0]
                        try:
                            target_id = int(target_id_str)
                            if target_id in game_state["players"]:
                                game_state["votes"][user_id] = target_id
                                send_message_to_chat(chat_id, f"Игрок id{user_id} проголосовал за id{target_id}.")
                            else:
                                send_message_to_chat(chat_id, "Этого игрока нет среди участников.")
                        except ValueError:
                            send_message_to_chat(chat_id, "Неверный формат id.")
                    else:
                        send_message_to_chat(chat_id, "Неверный формат команды !vote.")
                
                
                
                time.sleep(5)
                end_voting()

        else:
            
            if text == "!help":
                send_message_to_user(user_id, "Используйте команды в беседе!")
