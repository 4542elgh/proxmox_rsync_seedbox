import os
from model.torrent import Torrent
from pwd import getpwnam
from grp import getgrnam
import logging

class Permission:
    def __init__(self) -> None:
        self.logger = logging.getLogger()

    def update_permission(self, host_dir:str, paths: list[Torrent], chown_uid:str, chown_gid:str, chmod:str = ""):
        # Do not restrict user to use both chmod and chown, handle them separately for freedom
        if chmod:
            chmod_val = self._get_chmod_enums(chmod)
            for torrent in paths:
                parent_dir = os.path.join(os.path.join(host_dir, torrent.path))
                try:
                    os.chmod(parent_dir, chmod_val)
                except IOError as e:
                    self.logger.error("os.chmod raised an error: %s", e)

                for (new_base, dirs, files) in os.walk(parent_dir):
                    os.chmod(new_base, chmod_val)
                    # We dont do dirs, due to they will be new_base on next iteration
                    for file in files:
                        os.chmod(os.path.join(new_base, file), chmod_val)

        if (chown_uid and chown_gid):
            chown_uid_valid: int = 0
            chown_gid_valid: int = 0
            try:
                chown_uid_valid = int(chown_uid)
                chown_gid_valid = int(chown_gid)
            except ValueError:
                # This is good exception, lets fetch uid and gid
                (chown_uid_valid, chown_gid_valid) = self._get_uid_gid_from_name(chown_uid, chown_gid)

            for torrent in paths:
                parent_dir = os.path.join(os.path.join(host_dir, torrent.path))
                os.chown(parent_dir, chown_uid_valid, chown_gid_valid)
                for (new_base, dirs, files) in os.walk(parent_dir):
                    os.chown(new_base, chown_uid_valid, chown_gid_valid)
                    # We dont do dirs, due to they will be new_base on next iteration
                    for file in files:
                        os.chown(os.path.join(new_base, file), chown_uid_valid, chown_gid_valid)

    def _get_chmod_enums(self, chmod:str) -> int:
        # Owner = 7 * 64 = 448 = stat.S_IRWXU (Allow everything)
            #   = 4 * 64 = 256 = stat.S_IRUSR (Allow read)
            #   = 2 * 64 = 128 = stat.S_IWUSR (Allow write)
            #   = 1 * 64 = 64  = stat.S_IXUSR (Allow execute)
        # Group = permission * 8, everything else stays the same
            #   = 7 * 8 = 56   = stat.S_IRWXG (Allow everything)
        # Everyone = permission * 1, everything else stays the same
            #   = 7 * 1 = 7    = stat.S_IRWXO (Allow everything)

        # How this works
        # mutliplier is 3 digits long in bits
        # We have everyone permission with _ _ _ corresponding to r w x = 3 bits = gap of 8 in decimal aka an octal. but since its at the initial position we have 8^0
        # Next we have Group permission another _ _ _ = 3 bits = gap of 8 = 8^1 = multiple eveerythign in group permission by 8
        # Finally we have owner permission another _ _ _ = 3 bits = gap of 8 = 8^2 = multiple eveerythign in group permission by 64

        # Easier to work backwards
        aggregate_permission_val = 0
        rev_chmod = chmod[::-1]
        for (idx, perm) in enumerate(rev_chmod):
            aggregate_permission_val += int(perm) * pow(8, idx)

        return aggregate_permission_val


    def _get_uid_gid_from_name(self, uname:str, group:str) -> tuple[int, int]:
        return (getpwnam(uname).pw_uid, getgrnam(group).gr_gid)