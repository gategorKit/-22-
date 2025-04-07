import QtQuick 
import QtQuick.Window 2.15
import QtQuick.Controls 6.0
import QtQuick.Effects 6.0
import Qt5Compat.GraphicalEffects


Window {
    id: _root
    visible: true
    /*width: 1280
    height: 720
    minimumHeight: 720
    minimumWidth:1280*/
    
    visibility: Window.Maximized

    
    property bool flag: false
    property bool flagVisibleDistance: false


    // Связь с backend для обновлений
    Connections {
        target: backend
        function onUpdateTrigger() {
            cameraFeed.refresh();
            _canvas.requestPaint();
            compas.requestPaint();
            
            
        }
        function onDistTrigger() {
			flag = true;
			distanceItem.fadeIn();
			timer.start();
		}

    }

    // Камера
    Image {
        id: cameraFeed
        anchors.fill: parent
        source: "image://camera"
        fillMode: Image.PreserveAspectFit
        cache: false
		asynchronous: false
        anchors.centerIn: parent
        anchors.margins: 50 // Отступы по краям для изображения
        function refresh() {
            source = ""
            source = "image://camera"
        }
        /*MouseArea {
                anchors.fill: parent
                onClicked: { // При нажатии на изображение отобразить расстояние
                    flag = true;
                    distanceItem.fadeIn();  // Перерисовываем
                    timer.start(); // Запускаем таймер
                }
            }*/

        // Canvas для прицела
        Canvas {
            id: _canvas
            anchors.fill: cameraFeed
            anchors.topMargin: 20 // Отступы от краёв изображения
            property real crossSize: 20
            property string color: "#0af00a"

            onPaint: {
                var width = _canvas.width;
                var height = _canvas.height;
                var x = width / 2;
                var y = height / 2;
                var bx = x - width / 2;
                var by = y - height / 2;

                var ctx = getContext("2d");
                ctx.reset();

                // Прицел с обводкой
                // Чёрная обводка (толщина 6 пикселей)
                ctx.strokeStyle = "black";
                ctx.lineWidth = 6; // Увеличена толщина для явной обводки

                ctx.beginPath();
                ctx.moveTo(x, y - crossSize / 2 + pitch);
                ctx.lineTo(x, y + crossSize / 2 + pitch);
                ctx.stroke();

                ctx.beginPath();
                ctx.moveTo(x - crossSize / 2, y + pitch);
                ctx.lineTo(x + crossSize / 2, y + pitch);
                ctx.stroke();

                // Зелёная линия поверх (толщина 2 пикселя)
                ctx.strokeStyle = _canvas.color; // "#0af00a"
                ctx.lineWidth = 2;

                ctx.beginPath();
                ctx.moveTo(x, y - crossSize / 2 + pitch);
                ctx.lineTo(x, y + crossSize / 2 + pitch);
                ctx.stroke();

                ctx.beginPath();
                ctx.moveTo(x - crossSize / 2, y + pitch);
                ctx.lineTo(x + crossSize / 2, y + pitch);
                ctx.stroke();

                // Дополнительные линии с обводкой
                ctx.save(); // Сохраняем состояние canvas
                ctx.translate(x, y); // Переносим начало координат в центр
                ctx.rotate(roll * (Math.PI / 180)); // Поворачиваем систему координат

                // Чёрная обводка для доп линий (толщина 6 пикселей)
                ctx.strokeStyle = "black";
                ctx.lineWidth = 6; // Увеличена толщина для явной обводки

                // Левая линия
                ctx.beginPath();
                ctx.moveTo(-crossSize - 50, 0); // Начинаем слева
                ctx.lineTo(-crossSize - 300, 0); // Черта идёт влево
                ctx.stroke();

                // Правая линия
                ctx.beginPath();
                ctx.moveTo(crossSize + 50, 0); // Начинаем справа
                ctx.lineTo(crossSize + 300, 0); // Черта идёт вправо
                ctx.stroke();

                // Зелёная линия поверх (толщина 2 пикселя)
                ctx.strokeStyle = "#0af00a";
                ctx.lineWidth = 2;

                // Левая линия
                ctx.beginPath();
                ctx.moveTo(-crossSize - 50, 0); // Начинаем слева
                ctx.lineTo(-crossSize - 300, 0); // Черта идёт влево
                ctx.stroke();

                // Правая линия
                ctx.beginPath();
                ctx.moveTo(crossSize + 50, 0); // Начинаем справа
                ctx.lineTo(crossSize + 300, 0); // Черта идёт вправо
                ctx.stroke();

                ctx.restore(); // Восстанавливаем состояние canvas
            }
        }
        
        
        // Отображение компаса
        Canvas
        {
            id: compas
            anchors.fill: cameraFeed
            
            
            onPaint:
            {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height); // Очищаем холст
                var x = width / 2;
                var compassWidth = width*0.95;
               
                var compassX = x - compassWidth / 2;
                var compassY = 50;

                const count = 54; // Количество делений
                const stepWidth = width / count;
                const direction = Math.floor(degree / 90);
                const gradusi = degree % 90;

                let step_degree = compassX;

                // Левая часть компаса
                for (let i = degree - 25; i <= degree; i++) {
                    let xPosition = step_degree + stepWidth;
                    let lineLength = (i % 5 === 0) ? 15 : 7;
                    if (i === degree) lineLength = 30;

                    ctx.beginPath();
                    ctx.moveTo(xPosition, compassY);
                    ctx.lineTo(xPosition, compassY - lineLength);
                    ctx.strokeStyle = "#0af00a";
                    ctx.lineWidth = 3;
                    ctx.stroke();

                    // Отображение направлений (N, S, W, E)
                    if (i === 0 || i % 90 === 0) {
                        ctx.fillStyle = "#0af00a";
                        ctx.font = "14px sans-serif";
                        let text = ["N", "E", "S", "W"][Math.floor(i / 90)];

                        let textWidth = ctx.measureText(text).width;
                        ctx.fillText(text, xPosition - textWidth / 2, compassY + lineLength);
                    }

                    // Отображение чисел (только кратные 10)
                    if (i % 5 === 0 || i === degree) {
                        ctx.fillStyle = "#0af00a";
                        ctx.font = "14px sans-serif";
                        let text = ((i + 360) % 360).toString();
                        let textWidth = ctx.measureText(text).width;
                        ctx.fillText(text, xPosition - textWidth / 2, compassY - lineLength - 5);
                    }

                    step_degree += stepWidth;
                }

                step_degree += stepWidth * 25;

                // Правая часть компаса
                for (let i = degree + 24; i > degree; i--) {
                    let xPosition = step_degree - stepWidth;
                    let lineLength = (i % 5 === 0) ? 15 : 7;

                    ctx.beginPath();
                    ctx.moveTo(xPosition, compassY);
                    ctx.lineTo(xPosition, compassY - lineLength);
                    ctx.strokeStyle = "#0af00a";
                    ctx.lineWidth = 3;
                    ctx.stroke();

                    // Отображение направлений (N, S, W, E)
                    if (i === 0 || i % 90 === 0) {
                        ctx.fillStyle = "#0af00a";
                        ctx.font = "14px sans-serif";
                        let text = ["N", "E", "S", "W"][Math.floor(i / 90)];

                        let textWidth = ctx.measureText(text).width;
                        ctx.fillText(text, xPosition - textWidth / 2, compassY + lineLength);
                    }


                    // Отображение чисел (только кратные 10)
                    if (i % 5 === 0) {
                        ctx.fillStyle = "#0af00a";
                        ctx.font = "14px sans-serif";
                        let text = ((i + 360) % 360).toString();
                        let textWidth = ctx.measureText(text).width;
                        ctx.fillText(text, xPosition - textWidth / 2, compassY - lineLength - 5);
                    }

                    step_degree -= stepWidth;
                }

            }

        }
        
        // Карта
        Rectangle {
            anchors.right: cameraFeed.right
            anchors.bottom: cameraFeed.bottom
            anchors.bottomMargin: 20
            anchors.rightMargin: 60
            anchors.leftMargin: 20
            width: 200
            height: 200
            color: "transparent"
            
            
            Image {
                id: map
                anchors.fill: parent
                //source: "image://map_img"
                source: map_img
                visible: false  // Исходное изображение скрываем
                width: 200
                height: 200
                cache: false
            }
            
            Rectangle {
                id: mask
                anchors.fill: parent
                radius: 14
                
                visible: false  // Маска тоже скрыта
            }
            OpacityMask {
                anchors.fill: parent
                anchors.centerIn: parent
                source: map
                maskSource: mask
                width: 200
                height: 200
                visible: true
            }
            
            
        }
        // Таймер на 5 секунд для отображения расстояния
        Timer {
                    id: timer
                    interval: 5000 // 5 секунд
                    onTriggered: {
                        flag = false;
                    distanceItem.fadeOut(); // Перерисовка после скрытия
                    }
                }

        // Блок с расстоянием
        Item
        {
            id:distanceItem
            anchors.left: _canvas.horizontalCenter
            anchors.top: _canvas.verticalCenter
            anchors.leftMargin: 100
            anchors.bottomMargin: -200
            height:50
            width:250

            // Фон для текста
            Rectangle
            {
                id: distanceBackground
                height:50
                width:250
                color: "white"
                opacity: 0
                radius: 14
                //visible: false
            }

            // Текст с расстоянием
            Text
            {
                id: distanceText
                font.family: "sans-serif";
                font.pointSize: 14;
                color: "green"
               
                anchors.centerIn: distanceBackground
                opacity: 0
                
            }

            // Функция для плавного появления
            function fadeIn() {
                if (flag)
                {
                    
                    if (distanceInMM != -1 && distanceInMM != 8191 && distanceInMM != 32) {
                        distanceText.text = "Расстояние: " + distanceInMM + " мм";
                        if (flagVisibleDistance == false)
                        {
                            flagVisibleDistance = true
                            fadeInAnimation.start();
                        }
                    }
                }
            }

            // Функция для плавного исчезновения
            function fadeOut() {
                
                flagVisibleDistance = false
                fadeOutAnimation.start();
                
            }

            // Анимация появления
            ParallelAnimation {
                id: fadeInAnimation
                NumberAnimation {
                    target: distanceBackground
                    property: "opacity"
                    from: 0
                    to: 0.8 // Конечная прозрачность фона
                    duration: 700 // 0.5 секунды
                    easing.type: Easing.InOutQuad
                }
                NumberAnimation {
                    target: distanceText
                    property: "opacity"
                    from: 0
                    to: 1 // Полная видимость текста
                    duration: 700
                    easing.type: Easing.InOutQuad
                }
            }

            // Анимация исчезновения
            ParallelAnimation {
                id: fadeOutAnimation
                NumberAnimation {
                    target: distanceBackground
                    property: "opacity"
                    from: 0.8
                    to: 0
                    duration: 500
                    easing.type: Easing.InOutQuad
                }
                NumberAnimation {
                    target: distanceText
                    property: "opacity"
                    from: 1
                    to: 0
                    duration: 500
                    easing.type: Easing.InOutQuad
                }
            }

        }

        // Фон для кнопок
        Rectangle {
            id: buttons_zoom_camera_background
            anchors.left: _canvas.left
            anchors.bottom: _canvas.bottom
            anchors.bottomMargin: 20
            anchors.leftMargin: 60
            anchors.rightMargin: 20
            height: 150
            width: 120
            color: "white"
            opacity: 0.6
            radius: 14

            
        }

        Column {
                anchors.centerIn: buttons_zoom_camera_background  // Размещаем колонку по центру фона
                spacing: 15  // Отступ между кнопками

                Button {
                    icon.width: 50
                    icon.height: 50
                    id: zoomIn
                    icon.source: "img/zoom_in.png"
                    background: Rectangle { color: "transparent" }

                    onPressAndHold: backend.zoom_in()
                    onReleased: backend.zoom_stop()
                }

                Button {
                    id: zoomOut
                    icon.width: 50
                    icon.height: 50
                    icon.source: "img/zoom_out.png"
                    background: Rectangle { color: "transparent" }

                    onPressAndHold: backend.zoom_out()
                    onReleased: backend.zoom_stop()
                }
            }

        Rectangle {
            id: buttons_zoom_map_background
            anchors.left: buttons_zoom_camera_background.right
            anchors.bottom: cameraFeed.bottom
            anchors.bottomMargin: 20
            anchors.leftMargin: 10
            anchors.rightMargin: 20
            height: 150
            width: 120
            color: "white"
            opacity: 0.6
            radius: 14

            
        }

        Column {
                anchors.centerIn: buttons_zoom_map_background  // Размещаем колонку по центру фона
                spacing: 15  // Отступ между кнопками

                Button {
                    icon.width: 50
                    icon.height: 50
                    id: zoomInMap
                    //icon.source: "img/zoom_in_map.png"
                    //icon.color: "black"
                    background: Rectangle { color: "black" }
                    //enabled: false
                    onClicked: backend.zoom_in_map()
                }

                Button {
                    id: zoomOutMap
                    icon.width: 50
                    icon.height: 50
                    //icon.source: "img/zoom_out_map.png"
                    //icon.color: "black"
                    background: Rectangle { color: "black" }
                    //enabled: false
                    onClicked: backend.zoom_out_map()
                    
                }
            }


    }
}




