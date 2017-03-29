"""Provide models for new modmail."""
from ...const import API_PATH
from .base import RedditBase


class ModmailConversation(RedditBase):
    """A class for modmail conversations."""

    STR_FIELD = 'id'

    @staticmethod
    def _convert_conversation_objects(data, reddit):
        """Convert messages and mod actions to PRAW objects."""
        result = {'messages': [], 'modActions': []}
        for thing in data['conversation']['objIds']:
            key = thing['key']
            thing_data = data[key][thing['id']]
            result[key].append(reddit._objector.objectify(thing_data))
        return result

    @staticmethod
    def _convert_user_summary(data, reddit):
        """Convert dictionaries of recent user history to PRAW objects."""
        parsers = {'recentComments':
                   reddit._objector.parsers[reddit.config.kinds['comment']],
                   'recentConvos': ModmailConversation,
                   'recentPosts':
                   reddit._objector.parsers[reddit.config.kinds['submission']],
                   }
        for kind, parser in parsers.items():
            objects = []
            for thing_id, summary in data[kind].items():
                thing = parser(reddit, id=thing_id.rsplit('_', 1)[-1])
                if parser is not ModmailConversation:
                    del summary['permalink']
                for key, value in summary.items():
                    setattr(thing, key, value)
                objects.append(thing)
            # Sort by id, oldest to newest
            data[kind] = sorted(
                objects,
                key=lambda x: int(x.id, base=36), reverse=True)

    @classmethod
    def parse(cls, data, reddit):
        """Return an instance of ModmailConversation from ``data``.

        :param data: The structured data.
        :param reddit: An instance of :class:`.Reddit`.

        """
        conversation = data['conversation']

        conversation['authors'] = [reddit._objector.objectify(author)
                                   for author in conversation['authors']]
        conversation['owner'] = reddit._objector.objectify(
            conversation['owner'])

        if data['user']:
            cls._convert_user_summary(data['user'], reddit)
            conversation['user'] = reddit._objector.objectify(data['user'])
        conversation.update(cls._convert_conversation_objects(data, reddit))

        conversation = reddit._objector._snake_case_keys(conversation)

        return cls(reddit, _data=conversation)

    def __init__(self, reddit, id=None,  # pylint: disable=redefined-builtin
                 _data=None):
        """Construct an instance of the ModmailConversation object."""
        super(ModmailConversation, self).__init__(reddit, _data)

        self.id = id  # pylint: disable=invalid-name

    def _info_path(self):
        return API_PATH['modmail_conversation'].format(id=self.id)


class ModmailObject(RedditBase):
    """A base class for objects within a modmail conversation."""

    AUTHOR_ATTRIBUTE = 'author'
    STR_FIELD = 'id'

    def __setattr__(self, attribute, value):
        """Objectify the AUTHOR_ATTRIBUTE attribute."""
        if attribute == self.AUTHOR_ATTRIBUTE:
            value = self._reddit._objector.objectify(value)
        super(ModmailObject, self).__setattr__(attribute, value)


class ModmailAction(ModmailObject):
    """A class for moderator actions on modmail conversations."""


class ModmailMessage(ModmailObject):
    """A class for modmail messages."""