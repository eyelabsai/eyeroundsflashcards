'use client';

import { useMemo } from 'react';

interface TreatmentAccordionProps {
  treatment: string | null;
  loading: boolean;
}

interface Section {
  title: string;
  content: string;
  icon: string;
  colorClass: string;
}

export default function TreatmentAccordion({ treatment, loading }: TreatmentAccordionProps) {
  const sections = useMemo(() => {
    if (!treatment) return [];

    const result: Section[] = [];
    const lines = treatment.split('\n');
    let currentSection: Section | null = null;

    for (const line of lines) {
      // Match section headers like "1. Data Acquisition" or "**1. Data Acquisition**"
      const headerMatch = line.match(/^\**\s*(\d+)\.\s*([^*]+)/);
      
      if (headerMatch) {
        if (currentSection) {
          result.push(currentSection);
        }

        const num = headerMatch[1];
        const title = headerMatch[2].trim();

        let icon = '📋';
        let colorClass = 'bg-blue-50 text-blue-700';

        if (num === '1') {
          icon = '📊';
          colorClass = 'bg-blue-50 text-blue-700 border-blue-200';
        } else if (num === '2') {
          icon = '🔍';
          colorClass = 'bg-green-50 text-green-700 border-green-200';
        } else if (num === '3') {
          icon = '💊';
          colorClass = 'bg-purple-50 text-purple-700 border-purple-200';
        }

        currentSection = {
          title: `${icon} ${num}. ${title}`,
          content: '',
          icon,
          colorClass,
        };
      } else if (currentSection) {
        currentSection.content += line + '\n';
      }
    }

    if (currentSection) {
      result.push(currentSection);
    }

    // Split out Examiner Follow-up Questions only when it's a real section heading (not "follow-up" in middle of Management text)
    if (result.length > 0) {
      const lastSection = result[result.length - 1];
      // Match a line that is clearly the "Examiner Follow-up Questions" section header (start of line, optional **)
      const examinerHeaderRegex = /\n\s*(?:\*\*)?\s*Examiner\s+Follow-up\s+Questions?\s*(?:\*\*)?\s*\n/i;
      const examinerMatch = lastSection.content.match(examinerHeaderRegex);
      if (examinerMatch && examinerMatch.index !== undefined) {
        const idx = examinerMatch.index;
        const afterHeader = lastSection.content.slice(idx + examinerMatch[0].length).trim();
        lastSection.content = lastSection.content.slice(0, idx).trim();
        result.push({
          title: '❓ Examiner Follow-up Questions',
          content: afterHeader,
          icon: '❓',
          colorClass: 'bg-orange-50 text-orange-700 border-orange-200',
        });
      }
    }

    return result;
  }, [treatment]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white px-4 py-3 font-semibold">
          📋 Oral Boards Study Guide
        </div>
        <div className="p-6 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Generating study guide...</span>
        </div>
      </div>
    );
  }

  if (!treatment) {
    return (
      <div className="bg-gray-50 rounded-xl p-4 text-center text-gray-500">
        <p>Oral boards study guide will appear after reveal.</p>
        <p className="text-sm mt-1">Requires OpenAI API key to be configured.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden w-full min-w-0 flex-1 flex flex-col">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white px-3 py-2 font-semibold flex items-center gap-2 text-base">
        📋 Oral Boards Study Guide
      </div>

      {/* Accordion Sections - all expanded by default */}
      <div className="divide-y divide-gray-100 overflow-y-auto max-h-[calc(100vh-12rem)]">
        {sections.map((section, index) => (
          <details key={index} open={true} className="group">
            <summary
              className={`px-3 py-2 font-semibold cursor-pointer flex items-center gap-2 hover:brightness-95 transition-all text-base ${section.colorClass}`}
            >
              <span className="accordion-arrow text-xs">▶</span>
              {section.title}
            </summary>
            <div className="px-3 py-2 bg-gray-50 text-base leading-relaxed w-full min-w-0">
              <div
                className="prose prose-base max-w-none w-full study-guide-content"
                dangerouslySetInnerHTML={{ __html: formatContent(section.content) }}
              />
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}

function formatContent(content: string): string {
  // Bold "Label: description" in bullet points (e.g. "Visual acuity testing: Expect..." -> "**Visual acuity testing:** Expect...")
  let withBold = content.replace(
    /^[-•]\s+([A-Z][^:\n]{1,55}):\s+(.+)$/gm,
    (_, label, rest) => `- **${label.trim()}:** ${rest}`
  );
  // Bold first phrase in other bullet lines (e.g. "Measure visual acuity and refraction." or "Onset and duration of myopia; inquire...")
  withBold = withBold.replace(
    /^(-\s+)(?!\*\*)([A-Z][^.\n]{1,70}[.;])\s*(.*)$/gm,
    (_, bullet, phrase, rest) => `${bullet}**${phrase.trim()}**${rest ? ` ${rest}` : ''}`
  );
  // Convert markdown-style formatting to HTML
  let html = withBold
    // Bold
    .replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold text-gray-800">$1</strong>')
    // Bullet points
    .replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>')
    // Wrap consecutive li elements in ul
    .replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul class="list-disc list-inside space-y-0.5 my-1">$1</ul>')
    // Line breaks
    .replace(/\n/g, '<br>')
    // Clean up extra br after ul
    .replace(/<\/ul><br>/g, '</ul>')
    // Sub-headers (like "History:", "Exam Findings:")
    .replace(/^([A-Z][^:]+):\s*<br>/gm, '<h4 class="font-semibold text-gray-700 mt-1.5 mb-0.5 uppercase text-xs tracking-wide">$1</h4>');

  return html;
}