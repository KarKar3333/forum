# forum
# 1. Подготовка окружения  
  **Создайте виртуальное окружение**
  
    ```python -m venv venv```  

  **Активируйте виртуальное окружение**  
  
  __Windows:__
  
    venv\Scripts\activate    
  __Linux/Mac:__  
  
    source venv/bin/activate

# 2. Установка зависимостей  
    pip install -r requirements.txt  

# 3.Инициализация базы данных  
    flask db init
    flask db migrate
    flask db upgrate
  

# 4.Создание базы данных  
    python create_sample_data.py

# 5.Запуск сайта  
    python run.py  


__администратор:__  
  имя-admin  
  пароль-admin123  

__тестовый акаунт:__  
  имя-user1  
  пароль-user123  

P.S. все коды пишите в терминале в висуал студио код или в дрогой удобной программе   
так же работает в cmd но там необходимо входить в керенную папку 
