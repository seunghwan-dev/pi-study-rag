// All mock data for DEMO mode (Docker-free frontend demo)
// Text in Japanese, technical terms in English

import type {
  CategoryItem, ProgressResponse, AskResponse,
  SurveyResponse, QuizGenerateResponse, QuizEvaluateResponse,
  HistoryItem, PaperSchema, IngestResponse, FetchPaperResponse
} from "../types/study";

// Shared example queries (used by SearchSection chips + MOCK_*_ANSWERS lookup keys)
export const EXAMPLE_QUERIES = [
  "Small Data MLの一般的なアプローチは？",
  "Transfer Learningとは？",
  "Digital Twinの最新動向は？",
] as const;

export const mockCategories: CategoryItem[] = [
  { category: "small_data", label: "Small Data", chunk_count: 45 },
  { category: "digital_twin", label: "Digital Twin", chunk_count: 52 },
  { category: "physics_ml", label: "Physics+ML", chunk_count: 38 },
  { category: "transfer_learning", label: "Transfer Learning", chunk_count: 28 },
  { category: "manufacturing", label: "Manufacturing", chunk_count: 35 },
];

export const mockProgress: ProgressResponse = {
  overview: {
    total_papers: 5,
    total_chunks: 463,
    total_questions: 42,
    unique_chunks_cited: 156,
    overall_coverage: 0.34,
  },
  by_category: [
    { category: "small_data", label: "Small Data", chunk_count: 45, chunks_cited: 28, coverage: 0.62, question_count: 15, last_studied: "2026-04-15T10:30:00Z", days_since_last: 0, review_status: "recent" },
    { category: "digital_twin", label: "Digital Twin", chunk_count: 52, chunks_cited: 8, coverage: 0.15, question_count: 3, last_studied: "2026-04-01T08:00:00Z", days_since_last: 14, review_status: "review_recommended" },
    { category: "physics_ml", label: "Physics+ML", chunk_count: 38, chunks_cited: 35, coverage: 0.92, question_count: 20, last_studied: "2026-04-14T15:00:00Z", days_since_last: 1, review_status: "recent" },
    { category: "transfer_learning", label: "Transfer Learning", chunk_count: 28, chunks_cited: 12, coverage: 0.43, question_count: 8, last_studied: "2026-03-28T12:00:00Z", days_since_last: 18, review_status: "review_needed" },
    { category: "manufacturing", label: "Manufacturing", chunk_count: 35, chunks_cited: 0, coverage: 0.0, question_count: 0, last_studied: null, days_since_last: null, review_status: "not_started" },
  ],
  study_streak: { today: 5, this_week: 18, this_month: 42 },
  recommendation: { category: "digital_twin", message: "\u300CDigital Twin\u300D\u3092\u5FA9\u7FD2\u3057\u307E\u3057\u3087\u3046", reason: "14\u65E5\u9593\u672A\u5B66\u7FD2\u30FB\u30AB\u30D0\u30FC\u738715%" },
};

// ── Tutor / Socratic base answers (kept for backward compatibility) ──

export const mockTutorAnswer: AskResponse = {
  answer: "Small Data ML\u306E\u4E00\u822C\u7684\u306A\u30A2\u30D7\u30ED\u30FC\u30C1\u306B\u306F\u3001\u4EE5\u4E0B\u306E\u3088\u3046\u306A\u624B\u6CD5\u304C\u3042\u308A\u307E\u3059\u3002\n\n1. **Transfer Learning**: \u5927\u898F\u6A21\u30C7\u30FC\u30BF\u3067\u4E8B\u524D\u5B66\u7FD2\u3057\u305F\u30E2\u30C7\u30EB\u3092\u5C11\u91CF\u30C7\u30FC\u30BF\u3067\u5FAE\u8ABF\u6574\u3059\u308B\u65B9\u6CD5\u3002\n2. **Data Augmentation**: \u65E2\u5B58\u30C7\u30FC\u30BF\u3092\u5909\u63DB\u30FB\u62E1\u5F35\u3057\u3066\u5B66\u7FD2\u30C7\u30FC\u30BF\u3092\u5897\u3084\u3059\u624B\u6CD5\u3002\n3. **Few-Shot Learning**: \u6570\u4F8B\u306E\u30B5\u30F3\u30D7\u30EB\u304B\u3089\u6C4E\u5316\u80FD\u529B\u3092\u7372\u5F97\u3059\u308B\u624B\u6CD5\u3002\n\n\u51FA\u5178: Kraljevski et al. (2023) \"How to Do ML with Small Data\", p.3-5",
  hint: null, follow_up_question: null, has_direct_answer: true,
  sources: [
    { doc_title: "How to Do ML with Small Data", page_hint: "p.3", similarity: 0.94 },
    { doc_title: "How to Do ML with Small Data", page_hint: "p.5", similarity: 0.91 },
    { doc_title: "Revisiting Deep Learning for Tabular Data", page_hint: "p.8", similarity: 0.87 },
  ],
  mode: "tutor", model_mode: "fast", processing_time_sec: 8.2,
};

export const mockSocraticAnswer: AskResponse = {
  answer: null,
  hint: "\u30C7\u30FC\u30BF\u304C\u5C11\u306A\u3044\u72B6\u6CC1\u3067\u306F\u3001\u30E2\u30C7\u30EB\u306E\u300C\u6C4E\u5316\u80FD\u529B\u300D\u304C\u9375\u306B\u306A\u308A\u307E\u3059\u3002Kraljevski et al. (2023) \u306Ep.3\u3067\u306F\u30015\u3064\u306E\u30C7\u30FC\u30BF\u8AB2\u984C\u304C\u5206\u985E\u3055\u308C\u3066\u3044\u307E\u3059\u3002",
  follow_up_question: "\u3067\u306F\u3001\u3053\u308C\u3089\u306E\u8AB2\u984C\u306E\u3046\u3061\u3001\u88FD\u9020\u696D\u3067\u6700\u3082\u983B\u7E41\u306B\u767A\u751F\u3059\u308B\u306E\u306F\u3069\u308C\u3060\u3068\u601D\u3044\u307E\u3059\u304B\uFF1F",
  has_direct_answer: false,
  sources: [
    { doc_title: "How to Do ML with Small Data", page_hint: "p.3", similarity: 0.94 },
    { doc_title: "How to Do ML with Small Data", page_hint: "p.7", similarity: 0.88 },
  ],
  mode: "socratic", model_mode: "fast", processing_time_sec: 5.1,
};

// ── Query-specific lookup maps (DEMO mode) ──

export const MOCK_TUTOR_ANSWERS: Record<string, AskResponse> = {
  "Small Data MLの一般的なアプローチは？": mockTutorAnswer,
  "Transfer Learningとは？": {
    answer: "Transfer Learning（転移学習）とは、大規模データで事前学習したモデルの知識を、別のドメインやタスクに適応させる手法です。\n\n1. **Fine-tuning**: 事前学習済みモデルの全層または一部を、少量の目標データで再学習します。\n2. **Feature Extraction**: 事前学習モデルを固定特徴量抽出器として用い、上位に軽量な分類器を追加します。\n3. **Domain Adaptation**: ソースドメインとターゲットドメインの分布差を最小化するよう学習します。\n\n製造業の文脈では、ImageNet等で事前学習した汎用モデルを、限られた製品画像や工程ログへ転用することで、ゼロから学習するよりも大幅に少ないデータで実用精度を達成できます。\n\n出典: Gorishniy et al. (2021) \"Revisiting Deep Learning for Tabular Data\", p.8",
    hint: null, follow_up_question: null, has_direct_answer: true,
    sources: [
      { doc_title: "Revisiting Deep Learning for Tabular Data", page_hint: "p.8", similarity: 0.92 },
      { doc_title: "How to Do ML with Small Data", page_hint: "p.11", similarity: 0.86 },
    ],
    mode: "tutor", model_mode: "fast", processing_time_sec: 6.4,
  },
  "Digital Twinの最新動向は？": {
    answer: "Digital Twinの最新動向は、物理ベースモデリングと機械学習の融合（Hybrid Modeling）です。\n\n1. **PINN (Physics-Informed Neural Networks)**: 物理法則（偏微分方程式）を損失関数に組み込み、少量データでも物理整合性の高い予測を実現します。\n2. **Real-time Monitoring**: IoTセンサーデータを用い、製造工程のDigital Twinをオンラインで校正する研究が進んでいます。\n3. **Calibration with Small Data**: 実験データが限られる場合、転移学習やベイズ最適化でDigital Twinのパラメータを効率的に推定します。\n\n出典: Raissi et al. (2019) \"Physics-Informed Neural Networks for Manufacturing\", p.4",
    hint: null, follow_up_question: null, has_direct_answer: true,
    sources: [
      { doc_title: "Physics-Informed Neural Networks for Manufacturing", page_hint: "p.4", similarity: 0.93 },
      { doc_title: "Digital Twin Calibration with Limited Experimental Data", page_hint: "p.2", similarity: 0.89 },
    ],
    mode: "tutor", model_mode: "fast", processing_time_sec: 7.8,
  },
};

export const MOCK_SOCRATIC_ANSWERS: Record<string, AskResponse> = {
  "Small Data MLの一般的なアプローチは？": mockSocraticAnswer,
  "Transfer Learningとは？": {
    answer: null,
    hint: "大規模データで学習した知識を「どこまで」転移できるかが鍵です。ソースドメインとターゲットドメインの特徴分布が近いほど、浅い層の再利用で済みます。Gorishniy et al. (2021) p.8では、表形式データにおける転移可能性の限界が議論されています。",
    follow_up_question: "では、製造業の異なる製品ラインへモデルを転用する場合、最も注意すべき点は何だと思いますか？",
    has_direct_answer: false,
    sources: [
      { doc_title: "Revisiting Deep Learning for Tabular Data", page_hint: "p.8", similarity: 0.92 },
      { doc_title: "How to Do ML with Small Data", page_hint: "p.11", similarity: 0.83 },
    ],
    mode: "socratic", model_mode: "fast", processing_time_sec: 4.3,
  },
  "Digital Twinの最新動向は？": {
    answer: null,
    hint: "Digital Twinの価値は「予測精度」と「解釈可能性」のバランスにあります。純粋な機械学習モデルは精度が高くてもブラックボックスになりがちで、純粋な物理モデルは解釈可能ですが未知の挙動に弱いです。Raissi et al. (2019) p.4では、この2つの統合アプローチが提案されています。",
    follow_up_question: "物理モデルと機械学習モデルを統合する際、どちらの知見を優先すべきだと思いますか？その判断基準は何でしょうか？",
    has_direct_answer: false,
    sources: [
      { doc_title: "Physics-Informed Neural Networks for Manufacturing", page_hint: "p.4", similarity: 0.93 },
      { doc_title: "Digital Twin Calibration with Limited Experimental Data", page_hint: "p.5", similarity: 0.85 },
    ],
    mode: "socratic", model_mode: "fast", processing_time_sec: 5.7,
  },
};

export const mockSurveyResult: SurveyResponse = {
  monologue: [
    "\u3042\u306A\u305F\u306E\u77E5\u8B58\u30D9\u30FC\u30B9\u3092\u5206\u6790\u3057\u3066\u3044\u307E\u3059...",
    "Physics+ML(92%)\u304C\u6700\u3082\u5F37\u304F\u3001Digital Twin(15%)\u304C\u6700\u3082\u5F31\u3044\u3067\u3059\u3002",
    "\u6700\u8FD1\u306E\u5B66\u7FD2\u30D1\u30BF\u30FC\u30F3\u304B\u3089\u3001Small Data ML\u3078\u306E\u95A2\u5FC3\u304C\u6DF1\u307E\u3063\u3066\u3044\u307E\u3059\u3002",
    "4\u3064\u306E\u6226\u7565\u3067\u30AD\u30FC\u30EF\u30FC\u30C9\u3092\u751F\u6210\u3057\u307E\u3057\u305F\u3002",
    "arxiv\u30674\u3064\u306E\u5207\u308A\u53E3\u304B\u3089\u63A2\u7D22\u3057\u30018\u4EF6\u306E\u65B0\u7740\u8AD6\u6587\u3092\u767A\u898B\u3057\u307E\u3057\u305F\u3002",
    "\u3046\u30612\u4EF6\u304C\u3042\u306A\u305F\u306E\u65E2\u5B58\u77E5\u8B58\u3068\u63A5\u7D9A\u53EF\u80FD\u3067\u3059\u3002",
  ],
  analysis: {
    strongest: { category: "physics_ml", label: "Physics+ML", coverage: 0.92 },
    weakest: { category: "digital_twin", label: "Digital Twin", coverage: 0.15 },
    recent_trend: "Small Data ML",
    auto_keywords: [
      "digital twin calibration small data manufacturing",
      "small data active learning process optimization",
      "physics-informed transfer learning materials science",
      "quantum computing materials informatics emerging",
    ],
  },
  recommendations: [
    {
      paper: { title: "Digital Twin Calibration with Limited Experimental Data", authors: ["Zhang, L.", "Park, C.", "Yoon, S."], arxiv_id: "2604.01234", pdf_url: "https://arxiv.org/pdf/2604.01234", is_open_access: true },
      connection: "Digital Twin\u30AB\u30D0\u30FC\u738715%\u6539\u5584\u306B\u76F4\u7D50 \u2014 Small Data\u306E\u624B\u6CD5\u3092\u9069\u7528\u53EF\u80FD", target_category: "digital_twin", relevance: 0.91,
    },
    {
      paper: { title: "Active Learning for Manufacturing Quality with Few Samples", authors: ["Chen, W.", "Tanaka, K."], arxiv_id: "2603.05678", pdf_url: "https://arxiv.org/pdf/2603.05678", is_open_access: true },
      connection: "\u65E2\u5B58Small Data\u77E5\u8B58\u306E\u5EF6\u9577 \u2014 \u80FD\u52D5\u5B66\u7FD2\u306B\u3088\u308B\u52B9\u7387\u7684\u30C7\u30FC\u30BF\u53CE\u96C6", target_category: "small_data", relevance: 0.87,
    },
  ],
  total_found: 8, total_recommended: 2,
};

// ── Quiz (DEMO) — pool of 3 rotating questions + evaluations ──

export type MockQuiz = QuizGenerateResponse & { model_answer: string };

export const mockQuizGenerate: QuizGenerateResponse = {
  quiz_id: "demo-quiz-001",
  question: "Small Data\u74B0\u5883\u306B\u304A\u3044\u3066\u3001Transfer Learning\u304C\u6709\u52B9\u3067\u3042\u308B\u4E3B\u306A\u7406\u7531\u30922\u3064\u8AAC\u660E\u3057\u3066\u304F\u3060\u3055\u3044\u3002\u307E\u305F\u3001\u88FD\u9020\u696D\u3067\u306E\u5177\u4F53\u7684\u306A\u9069\u7528\u4F8B\u30921\u3064\u6319\u3052\u3066\u304F\u3060\u3055\u3044\u3002",
  source: { doc_title: "How to Do ML with Small Data", page_hint: "p.5 Section 3.2" },
  category: "small_data", difficulty: "intermediate",
};

export const mockQuizEvaluate: QuizEvaluateResponse = {
  score: "partially_correct",
  feedback: "Transfer Learning\u306E\u57FA\u672C\u7684\u306A\u5229\u70B9\u306F\u6B63\u3057\u304F\u8AAC\u660E\u3055\u308C\u3066\u3044\u307E\u3059\u3002\u305F\u3060\u3057\u3001\u88FD\u9020\u696D\u3067\u306E\u5177\u4F53\u4F8B\u304C\u3084\u3084\u62BD\u8C61\u7684\u3067\u3059\u3002",
  complete_answer: "Transfer Learning\u304C\u6709\u52B9\u306A\u7406\u7531: (1) \u5927\u898F\u6A21\u30C7\u30FC\u30BF\u3067\u7372\u5F97\u3057\u305F\u7279\u5FB4\u8868\u73FE\u3092\u5C11\u91CF\u30C7\u30FC\u30BF\u306B\u8EE2\u7528\u3067\u304D\u308B (2) \u5B66\u7FD2\u306E\u53CE\u675F\u304C\u65E9\u304F\u3001\u904E\u5B66\u7FD2\u30EA\u30B9\u30AF\u304C\u4F4E\u6E1B\u3055\u308C\u308B\u3002",
  source: "Kraljevski et al. (2023), p.5",
  mastery_update: "quiz_score saved",
};

export const MOCK_QUIZZES: MockQuiz[] = [
  {
    quiz_id: "demo-quiz-001",
    question: "Small Dataが機械学習で「少ない」とされる定量的な基準は何ですか？論文の定義に基づいて簡潔に答えてください。",
    source: { doc_title: "How to Do ML with Small Data", page_hint: "p.2 Section 2.1" },
    category: "small_data",
    difficulty: "basic",
    model_answer: "Kraljevski et al. (2023)の定義では、サンプル数がモデルパラメータ数の10倍未満である場合をSmall Dataとします。実務上の目安として、表形式データでは数百〜数千サンプル、画像データでは数千サンプル未満が該当し、この領域では過学習リスクが急激に高まります。",
  },
  {
    quiz_id: "demo-quiz-002",
    question: "Transfer Learningが有効である主な理由を2つ説明してください。また、製造業での具体的な適用例を1つ挙げてください。",
    source: { doc_title: "How to Do ML with Small Data", page_hint: "p.5 Section 3.2" },
    category: "transfer_learning",
    difficulty: "intermediate",
    model_answer: "有効な理由: (1) 大規模データで獲得した汎用特徴表現を少量データへ転用できる、(2) 学習収束が早く過学習リスクが低減される。製造業の適用例: ImageNetで事前学習したCNNを表面欠陥検査に転用し、数十枚の欠陥画像のみで実用精度を達成する。",
  },
  {
    quiz_id: "demo-quiz-003",
    question: "Physics-Informed Neural Networks (PINN) において、物理法則はどのように学習プロセスに組み込まれますか？従来のニューラルネットワークとの違いを述べてください。",
    source: { doc_title: "Physics-Informed Neural Networks for Manufacturing", page_hint: "p.4 Section 2.3" },
    category: "digital_twin",
    difficulty: "advanced",
    model_answer: "PINNでは偏微分方程式（PDE）の残差を損失関数に正則化項として加え、データ損失と物理損失を同時に最小化します。従来のNNがデータのみからパターンを学習するのに対し、PINNは物理整合性を帰納バイアスとして持つため、少量データでも外挿性能が高く、物理的に妥当な予測を得られます。",
  },
];

export const MOCK_EVALUATIONS: Record<string, QuizEvaluateResponse> = {
  "demo-quiz-001": {
    score: "partially_correct",
    feedback: "Small Dataの定量的基準の方向性は捉えられていますが、論文の具体的な比率（パラメータ数の10倍未満）に言及するとより正確になります。",
    complete_answer: "Kraljevski et al. (2023)はSmall Dataを「サンプル数がモデルパラメータ数の10倍未満」と定義しています。表形式データでは数百〜数千サンプル、画像データでは数千サンプル未満が目安で、この基準を下回るとモデルは訓練データに過学習し汎化性能が大きく低下します。",
    source: "Kraljevski et al. (2023), p.2 Section 2.1",
    mastery_update: "quiz_score saved",
  },
  "demo-quiz-002": mockQuizEvaluate,
  "demo-quiz-003": {
    score: "correct",
    feedback: "PINNの核となる仕組み（損失関数への物理法則組み込み）と従来手法との違いが明確に説明されています。優秀な回答です。",
    complete_answer: "PINNでは支配方程式（PDE）の残差を損失関数に正則化項として加えます。具体的には L_total = L_data + λ·L_physics の形でデータ損失（観測値との誤差）と物理損失（PDE残差）を同時に最小化します。従来のNNがブラックボックス的にパターン学習するのに対し、PINNは物理的整合性を保証する帰納バイアスを持つため、少量データでも外挿性能が高くノイズにも頑健です。",
    source: "Raissi et al. (2019), p.4 Section 2.3",
    mastery_update: "quiz_score saved",
  },
};

export const mockHistory: HistoryItem[] = [
  { history_id: "h1", question: "Small Data ML\u306E\u4E00\u822C\u7684\u306A\u30A2\u30D7\u30ED\u30FC\u30C1\u306F\uFF1F", answer_preview: "Small Data ML\u306E\u4E00\u822C\u7684\u306A\u30A2\u30D7\u30ED\u30FC\u30C1\u306B\u306F\u3001Transfer Learning\u3001Data Augmentation...", study_mode: "tutor", model_mode: "fast", category: "small_data", quiz_score: null, created_at: "2026-04-15T10:30:00Z" },
  { history_id: "h2", question: "Digital Twin\u306E\u5B9A\u7FA9\u3092\u8AAC\u660E\u3057\u3066\u304F\u3060\u3055\u3044", answer_preview: "", study_mode: "quiz", model_mode: "fast", category: "digital_twin", quiz_score: "partially_correct", created_at: "2026-04-15T09:15:00Z" },
  { history_id: "h3", question: "Physics-informed ML\u3068\u306F\uFF1F", answer_preview: "\u30D2\u30F3\u30C8: \u7269\u7406\u6CD5\u5247\u3092\u30E2\u30C7\u30EB\u306B\u7D44\u307F\u8FBC\u3080\u3053\u3068\u3067...", study_mode: "socratic", model_mode: "fast", category: "physics_ml", quiz_score: null, created_at: "2026-04-14T15:00:00Z" },
  { history_id: "h4", question: "Synthetic Data\u306E\u751F\u6210\u65B9\u6CD5\u306F\uFF1F", answer_preview: "\u5408\u6210\u30C7\u30FC\u30BF\u751F\u6210\u306B\u306F\u3001GANs\u3001VAE\u3001\u7269\u7406\u30B7\u30DF\u30E5\u30EC\u30FC\u30B7\u30E7\u30F3\u306A\u3069...", study_mode: "tutor", model_mode: "smart", category: "synthetic_data", quiz_score: null, created_at: "2026-04-13T11:00:00Z" },
  { history_id: "h5", question: "Transfer Learning\u306E\u9650\u754C\u306F\uFF1F", answer_preview: "", study_mode: "quiz", model_mode: "fast", category: "transfer_learning", quiz_score: "correct", created_at: "2026-04-12T16:30:00Z" },
];

export const mockArxivSearch: PaperSchema[] = [
  { arxiv_id: "2311.07126", title: "How to Do Machine Learning with Small Data? A Review", authors: ["Kraljevski, I.", "Ju, Y.C.", "Sipka, D."], abstract: "A review from an industrial perspective...", published: "2023-11", pdf_url: "https://arxiv.org/pdf/2311.07126", already_ingested: true },
  { arxiv_id: "2401.12345", title: "Few-Shot Process Optimization in Smart Manufacturing", authors: ["Park, J.", "Kim, S."], abstract: "We propose a few-shot learning framework...", published: "2024-01", pdf_url: "https://arxiv.org/pdf/2401.12345", already_ingested: false },
  { arxiv_id: "2402.67890", title: "Bayesian Active Learning for Quality Control with Limited Samples", authors: ["Weber, M.", "Chen, L."], abstract: "Active learning strategies for quality inspection...", published: "2024-02", pdf_url: "https://arxiv.org/pdf/2402.67890", already_ingested: false },
];

export const mockIngestResult: IngestResponse = {
  doc_id: "demo-doc-001",
  title: "Demo Paper \u2014 Small Data Approaches",
  doc_type: "paper",
  chunks_created: 160,
  chunks_filtered: 0,
  categories_detected: ["small_data", "transfer_learning", "manufacturing"],
  chunks_by_method: { pymupdf_text: 140, pymupdf_table: 12, vlm_figure: 8 },
  vlm_pages_processed: 3,
};

export const mockFetchResult: FetchPaperResponse = {
  doc_id: "demo-fetch-001",
  title: "Few-Shot Process Optimization",
  chunks_created: 85,
  chunks_filtered: 0,
  categories_detected: ["small_data", "manufacturing"],
  processing_time_sec: 28.5,
  chunks_by_method: { pymupdf_text: 70, pymupdf_table: 10, vlm_figure: 5 },
  vlm_pages_processed: 2,
};
