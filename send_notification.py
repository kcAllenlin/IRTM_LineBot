def send_notification(id):
    file = "analyisis.csv"
    f = open(file, "r")
    title = f.readline()
    for row in f.readlines():
        item = row.strip().split()
        if item[0] == user_company[id]:  #變數應該會隨存放位置不同而需要修改
            if item[3] == "n":
                print(f"您的公司：{user_company[id]}，今天有一篇新聞的情緒為負")
                print(f"網址：{item[2]}")
    f.close()
