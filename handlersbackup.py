import os
from telebot import types
from db import cursor, conn
from config import ADMIN_ID, UPLOAD_FOLDER
from telebot import TeleBot

user_states = {}
candidate_data = {}  # Для хранения данных кандидата во время добавления

def start_handlers(bot: TeleBot):

    @bot.message_handler(commands=['start'])
    def main_menu(message):
        user_id = message.from_user.id
        user_states[user_id] = 'main'
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_vote = types.KeyboardButton('🗳️ Голосовать')
        btn_admin = types.KeyboardButton('🔒 Админ-панель')
        markup.add(btn_vote, btn_admin)
        
        bot.send_message(message.chat.id, 
                         "*🎉 Добро пожаловать в голосование!* \n\n"
                         "Выберите опцию:", 
                         reply_markup=markup)

    # Обработчик выбора и голосования
    @bot.message_handler(func=lambda message: True)
    def handle_choice_and_vote(message):
        user_id = message.from_user.id
        current_state = user_states.get(user_id, 'main')

        if current_state == 'main':
            if message.text == '🗳️ Голосовать':
                vote_menu(message)
            elif message.text == '🔒 Админ-панель':
                admin_panel(message)
            else:
                bot.send_message(message.chat.id, "⚠️ *Неверный выбор.* Пожалуйста, выберите опцию из меню.")

        elif current_state == 'voting':
            username = message.from_user.username
            candidate_text = message.text.strip()
        
            # Отладочное сообщение
            bot.send_message(message.chat.id, f"Пользователь выбрал: {candidate_text}")
        
            # Проверка, голосовал ли пользователь ранее
            cursor.execute('SELECT * FROM votes WHERE user_id = ?', (user_id,))
            if cursor.fetchone():
                bot.send_message(message.chat.id, "❌ *Вы уже проголосовали!* Повторное голосование невозможно.")
                main_menu(message)
            else:
                # Проверка существования кандидата
                cursor.execute('SELECT * FROM candidates WHERE name = ?', (candidate_text,))
                candidate = cursor.fetchone()
        
                # Если кандидат найден
                if candidate:
                    # Отправляем сообщение о том, что голос был принят
                    cursor.execute('INSERT INTO votes (user_id, username, candidate) VALUES (?, ?, ?)', 
                                   (user_id, username, candidate_text))
                    conn.commit()
                    bot.send_message(message.chat.id, f"✅ *Спасибо за ваш голос!* Вы выбрали {candidate_text}.")
                    main_menu(message)
                else:
                    # Если кандидат не найден, выводим сообщение об ошибке
                    bot.send_message(message.chat.id, "⚠️ *Неверный выбор.* Попробуйте еще раз.")
                    vote_menu(message)  # Возвращаемся к меню голосования


        elif current_state.startswith('adding_'):
            # Обработка шагов добавления кандидата
            if current_state == 'adding_photo':
                process_candidate_photo(message)
            elif current_state == 'adding_name':
                process_candidate_name(message)
            elif current_state == 'adding_description':
                process_candidate_description(message)
            elif current_state == 'adding_link':
                process_candidate_link(message)
            else:
                bot.send_message(message.chat.id, "⚠️ *Неверное состояние. Пожалуйста, начните заново.*")
                user_states.pop(user_id, None)

        elif current_state == 'admin':
            if message.text == '🔙 Назад':
                main_menu(message)
            elif message.text == '➕ Добавить кандидата':
                add_candidate(message)
            elif message.text == '🗑️ Удалить все голоса':
                remove_votes(message)
            elif message.text == '🗑️ Удалить всех кандидатов':
                remove_candidates(message)
            else:
                bot.send_message(message.chat.id, "⚠️ *Неверный выбор.* Пожалуйста, выберите опцию из меню.")

    def vote_menu(message):
        markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)

        cursor.execute('SELECT name, photo_url FROM candidates')  # Удален gender
        candidates = cursor.fetchall()

        if candidates:
            for candidate, photo_url in candidates:
                markup.add(types.KeyboardButton(candidate))
            
            bot.send_message(message.chat.id, 
                             "*🎉 Пожалуйста, выберите кандидата, нажав на одну из кнопок ниже:*", 
                             reply_markup=markup)
            user_states[message.from_user.id] = 'voting'
        else:
            bot.send_message(message.chat.id, "❌ *Кандидаты отсутствуют!* Пожалуйста, добавьте кандидатов через админ-панель.")

    def admin_panel(message):
        if message.from_user.id == ADMIN_ID:
            user_states[message.from_user.id] = 'admin'
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn_add_candidate = types.KeyboardButton('➕ Добавить кандидата')
            btn_remove_votes = types.KeyboardButton('🗑️ Удалить все голоса')
            btn_remove_candidates = types.KeyboardButton('🗑️ Удалить всех кандидатов')
            btn_back = types.KeyboardButton('🔙 Назад')
            markup.add(btn_add_candidate, btn_remove_votes, btn_remove_candidates, btn_back)

            bot.send_message(message.chat.id, 
                             "🔒 *Добро пожаловать в админ-панель!*\n\n"
                             "Выберите опцию:", 
                             reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "🚫 *У вас нет прав для доступа к админ-панели!*")

    @bot.message_handler(func=lambda message: message.text == '➕ Добавить кандидата')
    def add_candidate(message):
        if message.from_user.id == ADMIN_ID:
            user_id = message.from_user.id
            user_states[user_id] = 'adding_photo'
            bot.send_message(message.chat.id, "📝 *Пожалуйста, загрузите фотографию кандидата:*")
        else:
            bot.send_message(message.chat.id, "🚫 *У вас нет прав для добавления кандидатов!*")

    def process_candidate_photo(message):
        user_id = message.from_user.id
        if message.content_type == 'photo' and user_states.get(user_id) == 'adding_photo':
            photo_id = message.photo[-1].file_id
            file_info = bot.get_file(photo_id)
            downloaded_file = bot.download_file(file_info.file_path)

            # Сохраняем фотографию в папку
            photo_filename = f"{user_id}_{photo_id}.jpg"
            photo_path = os.path.join(UPLOAD_FOLDER, photo_filename)
            with open(photo_path, 'wb') as new_file:
                new_file.write(downloaded_file)

            # Сохраняем путь к фото в словаре
            candidate_data[user_id] = {'photo_url': photo_path}

            user_states[user_id] = 'adding_name'
            bot.send_message(message.chat.id, "📝 *Пожалуйста, введите имя кандидата:*")
        else:
            bot.send_message(message.chat.id, "⚠️ *Пожалуйста, отправьте фотографию кандидата.*")

    def process_candidate_name(message):
        user_id = message.from_user.id
        if user_states.get(user_id) == 'adding_name':
            candidate_name = message.text.strip()
            if not candidate_name:
                bot.send_message(message.chat.id, "⚠️ *Имя кандидата не может быть пустым. Пожалуйста, введите имя кандидата:*")
                return

            candidate_data[user_id]['name'] = candidate_name

            user_states[user_id] = 'adding_description'
            bot.send_message(message.chat.id, "📖 *Пожалуйста, введите описание кандидата:*")
        else:
            bot.send_message(message.chat.id, "⚠️ *Неверный шаг. Пожалуйста, начните добавление кандидата заново.*")
            user_states.pop(user_id, None)
    
# Убедитесь, что остальная часть кода по добавлению кандидатов также обновлена


    def process_candidate_description(message):
        user_id = message.from_user.id
        if user_states.get(user_id) == 'adding_description':
            description = message.text.strip()
            candidate_data[user_id]['description'] = description

            user_states[user_id] = 'adding_link'
            bot.send_message(message.chat.id, "🔗 *Пожалуйста, введите ссылку на дополнительную информацию о кандидате:*")
        else:
            bot.send_message(message.chat.id, "⚠️ *Неверный шаг. Пожалуйста, начните добавление кандидата заново.*")
            user_states.pop(user_id, None)

    def process_candidate_link(message):
        user_id = message.from_user.id
        if user_states.get(user_id) == 'adding_link':
            link = message.text.strip()
            candidate_data[user_id]['link'] = link

            # Сохраняем данные в базе данных
            try:
                cursor.execute('''
                    INSERT INTO candidates (name, photo_url, description, link)
                    VALUES (?, ?, ?, ?)
                ''', (
                    candidate_data[user_id]['name'],
                    candidate_data[user_id]['photo_url'],
                    candidate_data[user_id]['description'],
                    candidate_data[user_id]['link']
                ))
                conn.commit()
                bot.send_message(message.chat.id, f"✅ *Кандидат {candidate_data[user_id]['name']} добавлен успешно!*")
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ *Произошла ошибка при добавлении кандидата:* {str(e)}")
            finally:
                # Очистка данных и состояния
                user_states.pop(user_id, None)
                candidate_data.pop(user_id, None)
        else:
            bot.send_message(message.chat.id, "⚠️ *Неверный шаг. Пожалуйста, начните добавление кандидата заново.*")
            user_states.pop(user_id, None)

    def remove_votes(message):
        if message.from_user.id == ADMIN_ID:
            cursor.execute('DELETE FROM votes')
            conn.commit()
            bot.send_message(message.chat.id, "🗑️ *Все голоса успешно удалены!*")
        else:
            bot.send_message(message.chat.id, "🚫 *У вас нет прав для удаления голосов!*")

    def remove_candidates(message):
        if message.from_user.id == ADMIN_ID:
            cursor.execute('DELETE FROM candidates')
            conn.commit()
            bot.send_message(message.chat.id, "🗑️ *Все кандидаты успешно удалены!*")
        else:
            bot.send_message(message.chat.id, "🚫 *У вас нет прав для удаления кандидатов!*")

    
    @bot.message_handler(content_types=['photo'])
    def handle_photos(message):
        user_id = message.from_user.id
        state = user_states.get(user_id)

        if state == 'adding_photo':
            process_candidate_photo(message)
        else:
            # Можно обрабатывать другие фотографии или игнорировать
            pass

