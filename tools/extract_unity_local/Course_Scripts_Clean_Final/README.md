# GTA Vice City Game Clone - Clean C# Scripts (Episodes 1 - 75)

تمت إعادة بناء وتنظيم وهندسة سكريبتات دورة **Mobile Game Development Tutorial (GTA Vice City Game Clone)** بالكامل ومطابقتها للكود في الفيديوهات ولقطات الإطارات (Candidate Frames) مع تصحيح كافة أخطاء التعرف البصري (OCR) وإزالة التكرارات الناتجة عن الدمج التلقائي.

---

## هيكلية السكريبتات والأنظمة (Project Structure)

### 1. نظام اللاعب والتحكم (Player System)
- [`PlayerMovement.cs`](Player/PlayerMovement.cs): حركة اللاعب، السرعة، الدوران، القفز، الجاذبية، وحالات السقوط والهبوط على الأرض. (الحلقات: 6, 7, 8, 13, 14, 15, 39, 46, 49, 71)
- [`InputManager.cs`](Player/InputManager.cs): استقبال المدخلات من لوحة المفاتيح والماوس ونظام الإدخال مع دعم كامل للـ Joystick وأزرار اللمس للموبايل. (الحلقات: 5, 6, 7, 8, 9, 11, 13, 15, 27, 28, 29, 30, 31, 39, 56, 57, 68, 69, 71, 73)
- [`PlayerManager.cs`](Player/PlayerManager.cs): منسق دورة حياة الكائن للاعب، الكاميرا، الحركة، وحالات قيادة المركبات. (الحلقات: 7, 11, 14, 15, 39, 71)
- [`AnimatorManager.cs`](Player/AnimatorManager.cs): التحكم في قيم ومتحولات Mecanim Animator وتنعيم الحركة وتشغيل الأنيميشن. (الحلقات: 8, 13, 14, 15)
- [`PlayerHealth.cs`](Player/PlayerHealth.cs): صحة اللاعب وتلقي الضرر وموت اللاعب وربط شريط الصحة UI. (الحلقة: 49)
- [`ResetBool.cs`](Player/ResetBool.cs): سكريبت `StateMachineBehaviour` لتصفير حالات الأنيميشن. (الحلقات: 14, 15)

### 2. نظام الكاميرا (Camera System)
- [`CameraManager.cs`](Camera/CameraManager.cs): كاميرا المنظور الثالث، تتبع اللاعب، تدوير الكاميرا، منع اختراق الجدران عبر SphereCast، التصويب (Aim Zoom)، وسكوب القناصة. (الحلقات: 9, 10, 11, 12, 14, 28, 30, 57, 59, 64, 68, 71, 73)
- [`CarCameraController.cs`](Camera/CarCameraController.cs): كاميرا ناعمة لملاحقة وتتبع السيارات والمركبات. (الحلقات: 40, 72, 75)
- [`MiniMapController.cs`](Camera/MiniMapController.cs): كاميرا الخريطة المصغرة (MiniMap) العلوية ومزامنة الاتجاه. (الحلقة: 52)

### 3. نظام إطلاق النار والأسلحة (Shooting System)
- [`ShootingController.cs`](Shooting/ShootingController.cs): نظام إطلاق النار بالـ Raycast، الضرر، الذخيرة، إعادة التعبئة (Reloading)، وميض الفوهة (Muzzle Flash)، وتأثيرات الارتطام، والتبديل بين الأسلحة. (الحلقات: 30, 31, 32, 33, 46, 47, 48, 60, 62, 71, 73)

### 4. متجر الأسلحة (Shop System)
- [`ShopSystem.cs`](Shop/ShopSystem.cs): واجهة متجر الأسلحة، شراء الأسلحة والذخيرة بخصم أموال اللاعب. (الحلقات: 26, 27, 28, 29, 74)
- [`ColliderAction.cs`](Shop/ColliderAction.cs): منطقة تفاعل الدخول لمتجر السلاح وإظهار زر الشراء. (الحلقات: 26, 27, 28, 29)

### 5. نظام المركبات (Vehicles System)
- [`CarController.cs`](Vehicles/CarController.cs): فيزياء قيادة السيارات عبر WheelCollider وعزم المحرك والمكابح وزاوية التوجيه وتحكم الموبايل. (الحلقات: 38, 72, 74)
- [`CarInteraction.cs`](Vehicles/CarInteraction.cs): نظام الدخول والخروج من السيارة وتبديل الكاميرا والتحكم. (الحلقات: 38, 39, 41)

### 6. نظام الذكاء الاصطناعي ونقاط المسار (AI & Waypoints System)
- [`Waypoint.cs`](AI/Waypoint.cs): عقد المسارات، الفروع، وتشتت العرض. (الحلقات: 17, 18, 19, 20)
- [`WaypointNavigator.cs`](AI/WaypointNavigator.cs): قيادة الذكاء الاصطناعي عبر المسارات والتنقل بين التفرعات. (الحلقات: 22, 35, 36, 37, 39, 44, 48)
- [`CharacterNavigatorScript.cs`](AI/CharacterNavigatorScript.cs): ذكاء المشاة، الحركة، تلقي رصاصات اللاعب، السقوط، والإبلاغ عن الجريمة للشرطة. (الحلقات: 22, 23, 33, 34, 39, 44, 46)
- [`AISpawner.cs`](AI/AISpawner.cs): توليد المشاة على نقاط المسار. (الحلقات: 24, 25, 48)
- [`CarNavigatorScript.cs`](AI/CarNavigatorScript.cs): ذكاء سيارات المرور والتوقف أمام العوائق والمشاة عبر Raycast. (الحلقات: 35, 36, 37)
- [`CarAISpawner.cs`](AI/CarAISpawner.cs): توليد سيارات المرور على المسارات. (الحلقات: 36, 37)

### 7. نظام الشرطة ومستوى المطلوبين (Police & Wanted System)
- [`WantedLevel.cs`](Police/WantedLevel.cs): إدارة نجوم المطلوبين (0 - 5 نجوم)، تسجيل الجرائم، ومؤقت زوال النجوم عند الهروب. (الحلقات: 42, 44, 45, 46, 51)
- [`PoliceOfficer.cs`](Police/PoliceOfficer.cs): ذكاء رجل الشرطة (دورية، مطاردة اللاعب المطلوب، إطلاق النار، تلقي الضرر، والموت). (الحلقات: 43, 44, 45, 46, 47, 48)
- [`PoliceWaypointNavigator.cs`](Police/PoliceWaypointNavigator.cs): مسارات دوريات الشرطة عبر NavMeshAgent. (الحلقات: 44, 47, 48)
- [`PoliceSpawner.cs`](Police/PoliceSpawner.cs): توليد الشرطة قرب اللاعب عند وجود نجوم مطلوبين. (الحلقة: 48)

### 8. نظام المهمات والقصة (Missions System)
- [`Mission1.cs`](Missions/Mission1.cs): المهمة الأولى (نقطة البداية، المشهد السينمائي Cutscene، اقتحام القصر، القضاء على الهدف، ومكافأة الأموال). (الحلقات: 58, 59, 60, 61, 62, 63)
- [`Character.cs`](Missions/Character.cs): الفئة الأساسية لشخصيات القصة والمهمات. (الحلقة: 60)
- [`Diaz.cs`](Missions/Diaz.cs): زعيم القصر ريكاردو دياز. (الحلقة: 62)
- [`Lance.cs`](Missions/Lance.cs): الرفيق لانس فانس وملاحقة تومي فيرجيتي. (الحلقة: 62)
- [`Guard.cs`](Missions/Guard.cs): حراس القصر والاشتباك المسلح. (الحلقة: 62)

### 9. نظام حفظ البيانات (Save & Load System)
- [`PlayerData.cs`](Data/PlayerData.cs): كائن البيانات القابل للحفظ والتسلسل (موقع اللاعب، الصحة، الأموال، المهمة الحالية، الأسلحة). (الحلقة: 65)
- [`SaveSystem.cs`](Data/SaveSystem.cs): الحفظ والتحميل الثنائي (Binary Serialization) في المسار الدائم. (الحلقات: 65, 66)

### 10. واجهات المستخدم وإدارة اللعبة (UI & GameManager)
- [`GameManager.cs`](UI/GameManager.cs): إدارة الأموال، حالة اللعبة، المهمة الحالية، وتنسيق الحفظ والاسترجاع وشاشة النهاية. (الحلقات: 23, 26, 27, 28, 29, 30, 31, 33, 42, 45, 50, 59, 60, 61, 62, 63, 64, 65, 66, 67, 70)
- [`HealthBar.cs`](UI/HealthBar.cs): شريط صحة اللاعب مع تدرج الألوان. (الحلقة: 49)
- [`PauseMenu.cs`](UI/PauseMenu.cs): إيقاف اللعبة، المتابعة، إعادة التشغيل، والعودة للقائمة الرئيسية. (الحلقات: 56, 73)
- [`MainMenuManager.cs`](UI/MainMenuManager.cs): القائمة الرئيسية، بدء اللعبة، تحميل الحفظ، لوحة الخيارات والتحكم بالصوت. (الحلقات: 53, 54, 55, 66)

### 11. أدوات المحرر (Unity Editor Tools)
- [`WaypointEditor.cs`](Editor/WaypointEditor.cs): محرر المسارات في نافذة الـ Inspector وإضافة النقاط والفروع بنقرة واحدة. (الحلقات: 20, 21)
- [`WaypointManagerWindow.cs`](Editor/WaypointManagerWindow.cs): نافذة مخصصة `EditorWindow` لإنشاء ورسم مسارات الـ Waypoints في Scene View. (الحلقات: 17, 18, 19, 20)
