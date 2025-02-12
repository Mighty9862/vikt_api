import socket
print(socket.gethostname())


try:    
            data = await websocket.receive_text()
            #name = json.loads(data)["name"]
            if (json.loads(data))["type"] == "name":                  # {"type":"name", "name":"test"}
                datas = await service.get_all_question()
                res = {"questions": [{"id": q.id, "chapter": q.chapter, "question": q.question} for q in datas]}
                

                await websocket.send_json(res)
            else: 
                await websocket.send_json({"username":"test", "score":"20"})
        except JSONDecodeError as e:
            await websocket.send_text(f'Входящие данные должны быть json формата: {str(e)}')
