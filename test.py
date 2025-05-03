import requests

def test_answers(status_url: str, answers_url: str) -> None:
    """
    status_url: str - API url for take game status;\n
    answers_url: str - API url for take answers for current question;
    
    """
    response = requests.post(status_url)

    if response.status_code != 200:
        print(f"Ошибка получения статуса: {response.status_code}\n{response.text}")
        exit()

    try:
        status_data = response.json()['status']
        question = status_data['current_question']
        answer = status_data['answer_for_current_question']
    except Exception as e:
        print(f"Ошибка парсинга: {e}")
        exit()

    
    print(f'\nТекущий вопрос: {question}\nТекущий ответ: {answer}\n')
    for team_num in range(1, 11):
        params = {
            'question': question,
            'username': f'Команда {team_num}',
            'answer': "Как назывался творческий коллектив художников" #answer
        }
        
        response = requests.post(
            url=answers_url,
            params=params,
            headers={'accept': 'application/json'}
        )

        if response.status_code == 200:
            print(f"Успешно: Команда {team_num}")
        else:
            print(f"Ошибка {response.status_code} для Команда {team_num}:\n{response.text}")


if __name__ == '__main__':

    status_url = "http://10.10.0.88:8000/api/v2/websocket/get_all_status"
    answers_url = "http://10.10.0.88:8000/api/v2/answers/"

    test_answers(status_url, answers_url)