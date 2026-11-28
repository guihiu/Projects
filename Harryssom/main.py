from AllWhatsPy import AllWhatsPy
print("oi")

awp = AllWhatsPy()

awp.conexao(server_host=True)
print("conec")
awp.ctt.encontrar_usuario(556299276057)
print("fe")
awp.msg.enviar_mensagem('Hello World')
print("ola")
awp.msg.analise.ultima_mensagem_chat()
