SQL и подготовка данных instrument_repository.py
Пути: C:\cabbage\script\instrument_repository.py, C:\cabbage\data\cabbagedb.db` — SQLite база данных
Логика подготовки данных для графика цены:
    Данные берутся из таблиц: price_history, futures_list.
    futures_list нудна что бы сопоставить колонки name и paper. Пример: Если я нажимаю на кнопку "Анализ" где name=GAZR,то по таблице futures_list это соответствует paper=GAZP.
    Подготовить данные для графика из таблицы price_history. Пример: Берутся все строки paper=GAZP.
    Здесь я не уверен, но мне кажется в массив загружается: date, high, low. Где date будет координата X, а high и low координата Y. 
    
Логика подготовки данных для графика ОИ:
    Данные беруться из таблицы: open_interest_history. Пример: Если я нажимаю на кнопку "Анализ" где name=GAZR, беруться все строки с name=GAZR.
    Для каждой строки производиться расчет: 
        private_long = float(row_data[1])
        private_shorts = float(row_data[2])
        legal_long = float(row_data[3])
        legal_shorts = float(row_data[4])

        max_fl = max(private_long, private_shorts)
        min_fl = min(private_long, private_shorts)
        coef_fl = round(max_fl / min_fl, 1) if min_fl != 0 else max_fl

        max_ul = max(legal_long, legal_shorts)
        min_ul = min(legal_long, legal_shorts)
        coef_ul = round(max_ul / min_ul, 1) if min_ul != 0 else max_ul
    Специальное ограничение:
        Если coef_fl и coef_ul >= 20 то coef_fl=20 и coef_ul=20
    Добовляется знак:
        Если private_long > private_shorts то coef_fl*1
        Если private_long < private_shorts то coef_fl*-1
        Если legal_long > legal_shorts то coef_ul*1
        Если legal_long < legal_shorts то coef_ul*-1
    Здесь я не уверен, но мне кажеться в массив загружается: date, coef_fl, coef_ul. Где date будет координата X, а coef_fl и coef_ul координата Y.
       
Напиши код для файла instrument_repository.py
////////////////////////////////////////////////////////////////////////////////////////////////////////////
Ок теперь надо соответственно написать код для: 
    price_graph_widget.py # Рисует график цены для выбранного инструмента.
        График будет в виде баров (горизонтальных полосок) верхняя точка high, нижняя low. 
        Цвет светло-синий, толщина 3px.
        По координате Y слева старые, справа новые данные по дате.
        Размещение баров: должно умещяться в окно графика, мне надо видеть визуал. 
        Задать максимальный отступ от верха, низа и правого края 10px. слева 5 px
    
    oi_graph_widget.py - Рисует график ОИ для выбранного инструмента.
        График будет в виде линий соеденяющих точки.
        coef_fl: цвет красная 
        coef_ul: цвет светло синяя  
        Толщина: 3px
        Дапазон по Y от -20 до 20
        Дапазон по X ос (слева) самой старой даты до новой
        
Путь C:\cabbage\app\ui\widgets\...
    

    
    
