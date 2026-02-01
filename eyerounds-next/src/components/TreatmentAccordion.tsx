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

    // Check for follow-up questions
    if (result.length > 0) {
      const lastSection = result[result.length - 1];
      const followUpRegex = /((?:examiner|follow.?up)[^\n]*(?:\n.+)*)/i;
      const followUpMatch = lastSection.content.match(followUpRegex);
      
      if (followUpMatch) {
        lastSection.content = lastSection.content.slice(0, followUpMatch.index);
        result.push({
          title: '❓ Examiner Follow-up Questions',
          content: followUpMatch[1],
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
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white px-4 py-3 font-semibold flex items-center gap-2">
        📋 Oral Boards Study Guide
      </div>

      {/* Accordion Sections */}
      <div className="divide-y divide-gray-100">
        {sections.map((section, index) => (
          <details key={index} open={index === 0} className="group">
            <summary
              className={`px-4 py-3 font-semibold cursor-pointer flex items-center gap-2 hover:brightness-95 transition-all ${section.colorClass}`}
            >
              <span className="accordion-arrow text-xs">▶</span>
              {section.title}
            </summary>
            <div className="px-4 py-3 bg-gray-50 text-sm leading-relaxed">
              <div
                className="prose prose-sm max-w-none"
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
  // Convert markdown-style formatting to HTML
  let html = content
    // Bold
    .replace(/\*\*([^*]+)\*\*/g, '<strong class="text-gray-800">$1</strong>')
    // Bullet points
    .replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>')
    // Wrap consecutive li elements in ul
    .replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul class="list-disc list-inside space-y-1 my-2">$1</ul>')
    // Line breaks
    .replace(/\n/g, '<br>')
    // Clean up extra br after ul
    .replace(/<\/ul><br>/g, '</ul>')
    // Sub-headers (like "History:", "Exam Findings:")
    .replace(/^([A-Z][^:]+):\s*<br>/gm, '<h4 class="font-semibold text-gray-700 mt-3 mb-1 uppercase text-xs tracking-wide">$1</h4>');

  return html;
}