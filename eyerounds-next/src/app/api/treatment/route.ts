import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const { title, description, contributor } = await request.json();
    
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      return NextResponse.json(
        { error: 'OpenAI API key not configured' },
        { status: 500 }
      );
    }

    const context = `Diagnosis: ${title}.
Findings/context: ${description || 'Not provided'}${
      contributor ? `
Contributor: ${contributor}.` : ''
    }`;

    const systemPrompt = `You are an ABO-style ophthalmology oral boards examiner. Cases are scored on Data Acquisition, Diagnosis, and Management. Examiners may ask: "Why is this information useful?" "How would you perform this surgery?" "What if that therapy didn't help?" They do not encourage, teach, or acknowledge right/wrong—they assess. Give output a candidate could use to prepare: clear, systematic, concise. Use bullet points and short paragraphs. Structure your response using the three ABO categories below.`;

    const userPrompt = `Given this ophthalmic case, provide a structured oral boards study guide.

${context}

Structure your response as:

**0. High-Yield Quick Answers**
- 5–8 bullets with short, oral-board-ready one-liners (diagnosis, key finding, top test, first-line treatment, critical complication, and one counseling point as applicable).
- Keep to rapid-fire responses; no long paragraphs.

**1. Data Acquisition**
- What relevant history to elicit (onset, progression, trauma, surgery, systemic risk factors).
- Important exam findings and ancillary testing to order (e.g., A/B scan, imaging, labs).

**2. Diagnosis**
- Differential diagnosis (what else to consider).
- Most likely diagnosis and key investigations that support it.

**3. Management**
- Safe, effective treatment plan: first-line and alternatives (dosing/renal adjustment if relevant), referral when appropriate.
- Potential complications of proposed treatment and expected outcomes/prognosis (cite trials if relevant, e.g., COMS).
- How to communicate the management plan and prognosis to the patient/family (clear, ethical).

End with 1–2 classic examiner follow-up questions (e.g., "How would you discuss prognosis with the patient?" "What if that didn't help? What other treatment might you consider?"). Be concise and board-style.`;

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: 'gpt-4o',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt },
        ],
        max_tokens: 1200,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('OpenAI API error:', error);
      return NextResponse.json(
        { error: 'Failed to generate treatment' },
        { status: 500 }
      );
    }

    const data = await response.json();
    const treatment = data.choices?.[0]?.message?.content?.trim() || '';

    return NextResponse.json({ treatment });
  } catch (error) {
    console.error('Treatment API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
