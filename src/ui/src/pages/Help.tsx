import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Book, ThumbsUp, ThumbsDown, ArrowLeft, ExternalLink } from 'lucide-react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const API_URL = 'http://localhost:8000';

interface HelpArticle {
  id: number;
  title: string;
  slug: string;
  category: string;
  summary: string;
  content?: string;
  icon?: string;
  featured: boolean;
  view_count: number;
  helpful_count?: number;
  not_helpful_count?: number;
  tags?: string[];
}

function Help() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedArticle, setSelectedArticle] = useState<HelpArticle | null>(null);
  const [feedbackGiven, setFeedbackGiven] = useState(false);
  const queryClient = useQueryClient();

  // Fetch categories
  const { data: categories = [] } = useQuery({
    queryKey: ['help-categories'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/help/categories`);
      return response.data;
    },
  });

  // Fetch articles
  const { data: articles = [], isLoading } = useQuery({
    queryKey: ['help-articles', selectedCategory, searchQuery],
    queryFn: async () => {
      if (searchQuery.trim().length >= 2) {
        const response = await axios.get(`${API_URL}/api/help/search`, {
          params: { q: searchQuery },
        });
        return response.data;
      }

      const params: any = {};
      if (selectedCategory) {
        params.category = selectedCategory;
      }

      const response = await axios.get(`${API_URL}/api/help/articles`, { params });
      return response.data;
    },
  });

  // Fetch featured articles
  const { data: featuredArticles = [] } = useQuery({
    queryKey: ['help-featured'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/help/articles`, {
        params: { featured: true },
      });
      return response.data;
    },
    enabled: !selectedCategory && !searchQuery,
  });

  // Fetch single article
  const { data: articleDetails } = useQuery({
    queryKey: ['help-article', selectedArticle?.slug],
    queryFn: async () => {
      if (!selectedArticle) return null;
      const response = await axios.get(`${API_URL}/api/help/articles/${selectedArticle.slug}`);
      return response.data;
    },
    enabled: !!selectedArticle,
  });

  // Mark article helpful mutation
  const markHelpfulMutation = useMutation({
    mutationFn: async ({ articleId, helpful }: { articleId: number; helpful: boolean }) => {
      await axios.post(`${API_URL}/api/help/articles/${articleId}/helpful`, null, {
        params: { helpful },
      });
    },
    onSuccess: () => {
      setFeedbackGiven(true);
      queryClient.invalidateQueries(['help-article', selectedArticle?.slug]);
    },
  });

  const handleArticleClick = (article: HelpArticle) => {
    setSelectedArticle(article);
    setFeedbackGiven(false);
  };

  const handleBack = () => {
    setSelectedArticle(null);
  };

  if (selectedArticle && articleDetails) {
    return (
      <div className="max-w-4xl mx-auto">
        <button
          onClick={handleBack}
          className="flex items-center text-blue-600 hover:text-blue-700 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Help
        </button>

        <div className="bg-white rounded-lg shadow p-8">
          <div className="mb-6">
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                {articleDetails.category}
              </span>
              <span>•</span>
              <span>{articleDetails.view_count} views</span>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-4">{articleDetails.title}</h1>
            <p className="text-lg text-gray-600">{articleDetails.summary}</p>
          </div>

          <div className="prose max-w-none mb-8">
            <ReactMarkdown>{articleDetails.content}</ReactMarkdown>
          </div>

          {articleDetails.tags && articleDetails.tags.length > 0 && (
            <div className="mb-6">
              <div className="flex flex-wrap gap-2">
                {articleDetails.tags.map((tag: string) => (
                  <span
                    key={tag}
                    className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="border-t pt-6">
            <p className="text-sm text-gray-700 mb-3">Was this article helpful?</p>
            {!feedbackGiven ? (
              <div className="flex gap-3">
                <button
                  onClick={() => markHelpfulMutation.mutate({ articleId: articleDetails.id, helpful: true })}
                  className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded hover:bg-green-200"
                >
                  <ThumbsUp className="h-4 w-4" />
                  Yes ({articleDetails.helpful_count || 0})
                </button>
                <button
                  onClick={() => markHelpfulMutation.mutate({ articleId: articleDetails.id, helpful: false })}
                  className="flex items-center gap-2 px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
                >
                  <ThumbsDown className="h-4 w-4" />
                  No ({articleDetails.not_helpful_count || 0})
                </button>
              </div>
            ) : (
              <p className="text-green-600">Thank you for your feedback!</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Book className="h-8 w-8" />
          Help & Documentation
        </h1>
        <p className="mt-2 text-sm text-gray-600">
          Find answers and learn how to get the most out of the system
        </p>
      </div>

      {/* Search */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search help articles..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Categories */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Browse by Category</h2>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedCategory === null
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All Articles
          </button>
          {categories.map((category: string) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                selectedCategory === category
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* Featured Articles */}
      {!searchQuery && !selectedCategory && featuredArticles.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Featured Articles</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {featuredArticles.map((article: HelpArticle) => (
              <div
                key={article.id}
                onClick={() => handleArticleClick(article)}
                className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 cursor-pointer hover:shadow-lg transition-shadow"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{article.title}</h3>
                <p className="text-sm text-gray-600 mb-3">{article.summary}</p>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span className="px-2 py-1 bg-white bg-opacity-70 rounded">{article.category}</span>
                  <span>{article.view_count} views</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Articles List */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          {searchQuery
            ? `Search Results (${articles.length})`
            : selectedCategory
            ? `${selectedCategory} (${articles.length})`
            : `All Articles (${articles.length})`}
        </h2>

        {isLoading ? (
          <div className="text-center py-8 text-gray-500">Loading...</div>
        ) : articles.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-500">No articles found</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow divide-y">
            {articles.map((article: HelpArticle) => (
              <div
                key={article.id}
                onClick={() => handleArticleClick(article)}
                className="p-6 cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2 hover:text-blue-600">
                      {article.title}
                    </h3>
                    <p className="text-sm text-gray-600 mb-3">{article.summary}</p>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span className="px-2 py-1 bg-gray-100 rounded">{article.category}</span>
                      <span>{article.view_count} views</span>
                    </div>
                  </div>
                  <ExternalLink className="h-5 w-5 text-gray-400 ml-4" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Help;
